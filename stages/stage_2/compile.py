from clvm import KEYWORD_TO_ATOM
from clvm_tools.binutils import disassemble
from clvm_tools.NodePath import LEFT, TOP

from .defaults import default_macro_lookup
from .helpers import brun, eval
from .mod import compile_mod


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


PASS_THROUGH_OPERATORS = set(KEYWORD_TO_ATOM.values())

for _ in "com opt".split():
    PASS_THROUGH_OPERATORS.add(_.encode("utf8"))


def compile_qq(args, macro_lookup, symbol_table, run_program, level=1):
    """
    (qq ATOM) => (q ATOM)
    (qq (unquote X)) => X
    (qq (a . B)) => (c (qq a) (qq B))
    """

    def com(sexp):
        return do_com_prog(sexp, macro_lookup, symbol_table, run_program)

    sexp = args.first()
    if not sexp.listp() or sexp.nullp():
        # (qq ATOM) => (q ATOM)
        return sexp.to([QUOTE_KW, sexp])

    if sexp.listp() and not sexp.first().listp():
        op = sexp.first().as_atom()
        if op == b"qq":
            subexp = compile_qq(sexp.rest(), macro_lookup, symbol_table, run_program, level+1)
            return com(sexp.to([CONS_KW, op, [CONS_KW, subexp, [QUOTE_KW, 0]]]))
        if op == b"unquote":
            if level == 1:
                # (qq (unquote X)) => X
                return com(sexp.rest().first())
            subexp = compile_qq(sexp.rest(), macro_lookup, symbol_table, run_program, level-1)
            return com(sexp.to([CONS_KW, op, [CONS_KW, subexp, [QUOTE_KW, 0]]]))

    # (qq (a . B)) => (c (qq a) (qq B))
    A = com(sexp.to([b"qq", sexp.first()]))
    B = com(sexp.to([b"qq", sexp.rest()]))
    return sexp.to([CONS_KW, A, B])


def compile_macros(args, macro_lookup, symbol_table, run_program):
    return args.to([QUOTE_KW, macro_lookup])


def compile_symbols(args, macro_lookup, symbol_table, run_program):
    return args.to([QUOTE_KW, symbol_table])


COMPILE_BINDINGS = {
    b"qq": compile_qq,
    b"macros": compile_macros,
    b"symbols": compile_symbols,
    b"lambda": compile_mod,
    b"mod": compile_mod,
}


def do_com_prog(prog, macro_lookup, symbol_table, run_program):
    """
    Turn the given program `prog` into a clvm program using
    the macros to do transformation.

    prog is an uncompiled s-expression.

    Return a new expanded s-expression PROG_EXP that is equivalent by rewriting
    based upon the operator, where "equivalent" means

    ((c (com (q PROG) (MACROS)) ARGS)) == ((c (q PROG_EXP) ARGS))
    for all ARGS.

    Also, (opt (com (q PROG) (MACROS))) == (opt (com (q PROG_EXP) (MACROS)))
    """

    # quote atoms
    if prog.nullp() or not prog.listp():
        atom = prog.as_atom()
        if atom == b"@":
            return prog.to(TOP.as_path())
        for pair in symbol_table.as_iter():
            symbol, value = pair.first(), pair.rest().first()
            if symbol == atom:
                return prog.to(value)

        return prog.to([QUOTE_KW, prog])

    operator = prog.first()
    if operator.listp():
        # (com ((OP) . RIGHT)) => ((c (com (q OP)) 1))
        inner_exp = eval(prog.to([b"com", [
            QUOTE_KW, operator], [QUOTE_KW, macro_lookup], [QUOTE_KW, symbol_table]]), TOP.as_path())
        return prog.to([inner_exp])

    as_atom = operator.as_atom()

    for macro_pair in macro_lookup.as_iter():
        macro_name = macro_pair.first().as_atom()
        if macro_name == as_atom:
            macro_code = macro_pair.rest().first()
            post_prog = brun(macro_code, prog.rest())
            return eval(post_prog.to(
                [b"com", post_prog, [QUOTE_KW, macro_lookup], [QUOTE_KW, symbol_table]]), TOP.as_path())

    if as_atom in COMPILE_BINDINGS:
        f = COMPILE_BINDINGS[as_atom]
        post_prog = f(prog.rest(), macro_lookup, symbol_table, run_program)
        return eval(prog.to([QUOTE_KW, post_prog]), TOP.as_path())

    if operator == QUOTE_KW:
        return prog

    compiled_args = [do_com_prog(_, macro_lookup, symbol_table, run_program) for _ in prog.rest().as_iter()]

    r = prog.to([operator] + compiled_args)

    if as_atom in PASS_THROUGH_OPERATORS or as_atom.startswith(b"_"):
        return r

    for (symbol, value) in symbol_table.as_python():
        if symbol == b"*":
            return r
        if symbol == as_atom:
            new_args = eval(
                prog.to([b"opt", [b"com",
                                  [QUOTE_KW, [b"list"] + list(prog.rest().as_iter())],
                                  [QUOTE_KW, macro_lookup],
                                  [QUOTE_KW, symbol_table]]]), TOP.as_path())
            r = prog.to([[CONS_KW, value, [CONS_KW, LEFT.as_path(), new_args]]])
            return r

    raise SyntaxError(
        "can't compile %s, unknown operator" %
        disassemble(prog))


def make_do_com(run_program):

    def do_com(sexp):
        prog = sexp.first()
        symbol_table = sexp.null()
        if not sexp.rest().nullp():
            macro_lookup = sexp.rest().first()
            if not sexp.rest().rest().nullp():
                symbol_table = sexp.rest().rest().first()
        else:
            macro_lookup = default_macro_lookup(run_program)
        return 1, do_com_prog(prog, macro_lookup, symbol_table, run_program)

    return do_com
