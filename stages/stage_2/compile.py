from clvm import KEYWORD_TO_ATOM
from clvm_tools.binutils import disassemble
from clvm_tools.NodePath import LEFT, TOP

from .defaults import default_macro_lookup
from .helpers import brun, eval, quote
from .mod import compile_mod

QUOTE_ATOM = KEYWORD_TO_ATOM["q"]
APPLY_ATOM = KEYWORD_TO_ATOM["a"]
CONS_ATOM = KEYWORD_TO_ATOM["c"]

PASS_THROUGH_OPERATORS = set(KEYWORD_TO_ATOM.values())

for _ in "com opt".split():
    PASS_THROUGH_OPERATORS.add(_.encode("utf8"))


def compile_qq(args, macro_lookup, symbol_table, run_program, level=1):
    """
    (qq ATOM) => (q . ATOM)
    (qq (unquote X)) => X
    (qq (a . B)) => (c (qq a) (qq B))
    """

    def com(sexp):
        return do_com_prog(sexp, macro_lookup, symbol_table, run_program)

    sexp = args.first()
    if not sexp.listp() or sexp.nullp():
        # (qq ATOM) => (q . ATOM)
        return sexp.to(quote(sexp))

    if sexp.listp() and not sexp.first().listp():
        op = sexp.first().as_atom()
        if op == b"qq":
            subexp = compile_qq(sexp.rest(), macro_lookup, symbol_table, run_program, level+1)
            return com(sexp.to([CONS_ATOM, op, [CONS_ATOM, subexp, quote(0)]]))
        if op == b"unquote":
            if level == 1:
                # (qq (unquote X)) => X
                return com(sexp.rest().first())
            subexp = compile_qq(sexp.rest(), macro_lookup, symbol_table, run_program, level-1)
            return com(sexp.to([CONS_ATOM, op, [CONS_ATOM, subexp, quote(0)]]))

    # (qq (a . B)) => (c (qq a) (qq B))
    A = com(sexp.to([b"qq", sexp.first()]))
    B = com(sexp.to([b"qq", sexp.rest()]))
    return sexp.to([CONS_ATOM, A, B])


def compile_macros(args, macro_lookup, symbol_table, run_program):
    return args.to(quote(macro_lookup))


def compile_symbols(args, macro_lookup, symbol_table, run_program):
    return args.to(quote(symbol_table))


COMPILE_BINDINGS = {
    b"qq": compile_qq,
    b"macros": compile_macros,
    b"symbols": compile_symbols,
    b"lambda": compile_mod,
    b"mod": compile_mod,
}


# Transform "quote" to "q" everywhere. Note that quote will not be compiled if behind qq.
# Overrides symbol table defns.
def lower_quote(prog, macro_lookup=None, symbol_table=None, run_program=None):
    if prog.nullp():
        return prog

    if prog.listp():
        if prog.first().as_atom() == b"quote":
            # Note: quote should have exactly one arg, so the length of
            # quoted list should be 2: "(quote arg)"
            if not prog.rest().rest().nullp():
                raise SyntaxError("Compilation error while compiling [%s]. quote takes exactly one argument." %
                                      disassemble(prog))
            return prog.to(quote(lower_quote(prog.rest().first())))
        else:
            return prog.to((lower_quote(prog.first()), lower_quote(prog.rest())))
    else:
        return prog

def do_com_prog(prog, macro_lookup, symbol_table, run_program):
    """
    Turn the given program `prog` into a clvm program using
    the macros to do transformation.

    prog is an uncompiled s-expression.

    Return a new expanded s-expression PROG_EXP that is equivalent by rewriting
    based upon the operator, where "equivalent" means

    (a (com (q PROG) (MACROS)) ARGS) == (a (q PROG_EXP) ARGS)
    for all ARGS.

    Also, (opt (com (q PROG) (MACROS))) == (opt (com (q PROG_EXP) (MACROS)))
    """

    # lower "quote" to "q"
    prog = lower_quote(prog, macro_lookup, symbol_table, run_program)

    # quote atoms
    if prog.nullp() or not prog.listp():
        atom = prog.as_atom()
        if atom == b"@":
            return prog.to(TOP.as_path())
        for pair in symbol_table.as_iter():
            symbol, value = pair.first(), pair.rest().first()
            if symbol == atom:
                return prog.to(value)

        return prog.to(quote(prog))

    operator = prog.first()
    if operator.listp():
        # (com ((OP) . RIGHT)) => (a (com (q OP)) 1)
        inner_exp = eval(prog.to([b"com",
            quote(operator), quote(macro_lookup), quote(symbol_table)]), TOP.as_path())
        return prog.to([inner_exp])

    as_atom = operator.as_atom()

    for macro_pair in macro_lookup.as_iter():
        macro_name = macro_pair.first().as_atom()
        if macro_name == as_atom:
            macro_code = macro_pair.rest().first()
            post_prog = brun(macro_code, prog.rest())
            return eval(post_prog.to(
                [b"com", post_prog, quote(macro_lookup), quote(symbol_table)]), TOP.as_short_path())

    if as_atom in COMPILE_BINDINGS:
        f = COMPILE_BINDINGS[as_atom]
        post_prog = f(prog.rest(), macro_lookup, symbol_table, run_program)
        return eval(prog.to(quote(post_prog)), TOP.as_path())

    if operator == QUOTE_ATOM:
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
                                  quote([b"list"] + list(prog.rest().as_iter())),
                                  quote(macro_lookup),
                                  quote(symbol_table)]]), TOP.as_path())
            r = prog.to([APPLY_ATOM, value, [CONS_ATOM, LEFT.as_path(), new_args]])
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
