from clvm import KEYWORD_TO_ATOM
from clvm_tools.binutils import disassemble

from .defaults import default_macro_lookup
from .helpers import brun, eval
from .mod import compile_defmacro, compile_mod


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]
ARGS_KW = KEYWORD_TO_ATOM["a"]


PASS_THROUGH_OPERATORS = set(
    KEYWORD_TO_ATOM[_] for _ in
    ("e a i c f r l x = sha256 + - * . "
     "wrap unwrap point_add pubkey_for_exp").split()
)

for _ in "com opt".split():
    PASS_THROUGH_OPERATORS.add(_.encode("utf8"))


def compile_list(args, macro_lookup):
    """
    (list) => ()
    (list (a @B) => (c a (list @B)))
    """
    if args.nullp():
        # (list) => ()
        return args

    # (list (a @B) => (c a (list @B)))
    return args.to([
        CONS_KW,
        args.first(),
        [b"list"] + list(args.rest().as_iter())])


def compile_function(args, macro_lookup):
    """
    "function" is used in front of a constant uncompiled
    program to indicate we want this program literal to be
    compiled and quoted, so it can be passed as an argument
    to a compiled clvm program.

    EG: (function (+ 20 (a))) should return (+ (q 20) (a)) when run.
    Thus (opt (com (q (function (+ 20 (a))))))
    should return (q (+ (q 20) (a)))

    (function PROG) => (opt (com (q PROG) (q MACROS)))

    We have to use "opt" as (com PROG) might leave
    some partial "com" operators in there and our
    goals is to compile PROG as much as possible.
    """
    prog = args.first()
    return args.to([b"opt", [b"com", [QUOTE_KW, prog], [QUOTE_KW, macro_lookup]]])


def compile_qq(args, macro_lookup, level=1):
    """
    (qq ATOM) => (q ATOM)
    (qq (unquote X)) => X
    (qq (a . B)) => (c (qq a) (qq B))
    """
    sexp = args.first()
    if not sexp.listp() or sexp.nullp():
        # (qq ATOM) => (q ATOM)
        return sexp.to([QUOTE_KW, sexp])

    if sexp.listp() and not sexp.first().listp():
        op = sexp.first().as_atom()
        if op == b"qq":
            subexp = compile_qq(sexp.rest(), macro_lookup, level+1)
            return sexp.to([b"list", op, subexp])
        if op == b"unquote":
            if level == 1:
                # (qq (unquote X)) => X
                return sexp.rest().first()
            subexp = compile_qq(sexp.rest(), macro_lookup, level-1)
            return sexp.to([b"list", op, subexp])

    # (qq (a . B)) => (c (qq a) (qq B))
    return sexp.to([CONS_KW, [b"qq", sexp.first()], [b"qq", sexp.rest()]])


COMPILE_BINDINGS = {
    b"list": compile_list,
    b"function": compile_function,
    b"qq": compile_qq,
    b"lambda": compile_mod,
    b"defmacro": compile_defmacro,
    b"mod": compile_mod,
}


def do_com_prog(prog, macro_lookup):
    """
    Turn the given program `prog` into a clvm program using
    the macros to do transformation.

    prog is an uncompiled s-expression.

    Return a new expanded s-expression PROG_EXP that is equivalent by rewriting
    based upon the operator, where "equivalent" means

    (e (com (q PROG) (MACROS)) ARGS) == (e (q PROG_EXP) ARGS)
    for all ARGS.

    Also, (opt (com (q PROG) (MACROS))) == (opt (com (q PROG_EXP) (MACROS)))
    """

    # quote atoms
    if prog.nullp() or not prog.listp():
        return prog.to([QUOTE_KW, prog])

    operator = prog.first()
    if operator.listp():
        # (com ((OP) . RIGHT)) => ((c (com (q OP)) (a)))
        inner_exp = eval(prog.to([b"com", [
            QUOTE_KW, operator], [QUOTE_KW, macro_lookup]]), [ARGS_KW])
        return prog.to([inner_exp])

    as_atom = operator.as_atom()

    for macro_pair in macro_lookup.as_iter():
        macro_name = macro_pair.first()
        if macro_name.as_atom() == as_atom:
            macro_code = macro_pair.rest().first()
            post_prog = brun(macro_code, prog.rest())
            return eval(post_prog.to([b"com", post_prog, [QUOTE_KW, macro_lookup]]), [ARGS_KW])

    if as_atom in COMPILE_BINDINGS:
        f = COMPILE_BINDINGS[as_atom]
        post_prog = f(prog.rest(), macro_lookup)
        return eval(post_prog.to([b"com", [QUOTE_KW, post_prog], [QUOTE_KW, macro_lookup]]), [ARGS_KW])

    if operator == QUOTE_KW:
        return prog

    if as_atom not in PASS_THROUGH_OPERATORS:
        raise SyntaxError(
            "can't compile %s, unknown operator" %
            disassemble(prog))

    new_args = prog.to([[b"com", [
        QUOTE_KW, _], [QUOTE_KW, macro_lookup]] for _ in prog.rest().as_iter()])
    return prog.to([operator] + [
        eval(_, [ARGS_KW]) for _ in new_args.as_iter()])


def do_com(sexp, eval_f):
    prog = sexp.first()
    if not sexp.rest().nullp():
        macro_lookup = sexp.rest().first()
    else:
        macro_lookup = default_macro_lookup(eval_f)
    return do_com_prog(prog, macro_lookup)
