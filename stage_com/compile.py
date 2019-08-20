from clvm import KEYWORD_TO_ATOM
from opacity.binutils import disassemble

from .lambda_ import compile_lambda, compile_defmacro
from .macros import default_macro_lookup
from .mod import compile_mod


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]
EVAL_KW = KEYWORD_TO_ATOM["e"]
ARGS_KW = KEYWORD_TO_ATOM["a"]


PASS_THROUGH_OPERATORS = set(
    KEYWORD_TO_ATOM[_] for _ in
    ("e a i c f r l x = sha256 + - * . "
     "wrap unwrap point_add pubkey_for_exp").split()
)

for _ in "com opt exp mac".split():
    PASS_THROUGH_OPERATORS.add(_.encode("utf8"))


def mark_uncompiled(prog, args=[ARGS_KW]):
    """
    PROG => (e (com (q PROG) (mac)) ARGS)

    The result can be evaluated with the stage_com eval_f
    function.
    """
    return prog.to([
        EVAL_KW, [b"com", [QUOTE_KW, prog], [b"mac"]], args])


def mark_expanded(prog):
    """
    PROG => (e (com (q PROG) (mac)) ARGS)

    The result can be evaluated with the stage_com eval_f
    function.
    """
    args = [ARGS_KW]
    return prog.to([
        EVAL_KW, [b"com", prog, [b"mac"]], args])


def brun(prog, args):
    return prog.to([
        EVAL_KW, [QUOTE_KW, prog], [QUOTE_KW, args]])


def compile_list(args):
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


def compile_function(args):
    """
    "function" is used in front of a constant uncompiled
    program to indicate we want this program literal to be
    compiled and quoted, so it can be passed as an argument
    to a compiled clvm program.

    EG: (function (+ 20 (a))) should return (+ (q 20) (a)) when run.
    Thus (opt (com (q (function (+ 20 (a))))))
    should return (q (+ (q 20) (a)))

    (function PROG) => (opt (com (q PROG) (mac)))

    We have to use "opt" as (com PROG) might leave
    some partial "com" operators in there and our
    goals is to compile PROG as much as possible.
    """
    prog = args.first()
    inner = args.to([b"opt", [b"com", [QUOTE_KW, prog], [b"mac"]]])
    return mark_uncompiled(inner)


def compile_qq(args):
    """
    (qq ATOM) => (q ATOM)
    (qq (unquote X)) => X
    (qq (a . B)) => (c (qq a) (qq B))
    """
    sexp = args.first()
    if not sexp.listp() or sexp.nullp():
        # (qq ATOM) => (q ATOM)
        return sexp.to([QUOTE_KW, sexp])

    if (sexp.listp() and not sexp.first().listp()
            and sexp.first().as_atom() == b"unquote"):
        # (qq (unquote X)) => X
        return sexp.rest().first()

    # (qq (a . B)) => (c (qq a) (qq B))
    return sexp.to([CONS_KW, [b"qq", sexp.first()], [b"qq", sexp.rest()]])


COMPILE_BINDINGS = {
    b"list": compile_list,
    b"function": compile_function,
    b"qq": compile_qq,
    b"lambda": compile_lambda,
    b"defmacro": compile_defmacro,
    b"mod": compile_mod,
}


def do_exp_prog(prog, macro_lookup):
    """
    prog is an uncompiled s-expression.

    Return a new expanded s-expression PROG_EXP that is equivalent by rewriting
    based upon the operator, where "equivalent" means

    (e (com (q PROG) (mac)) ARGS) == (e (com (q PROG_EXP) (mac)) ARGS)
    for all ARGS.

    Also, (opt (com (q PROG) (mac))) == (opt (com (q PROG_EXP) (mac)))
    for all ARGS.
    """

    # quote atoms
    if prog.nullp() or not prog.listp():
        return prog.to([QUOTE_KW, [QUOTE_KW, prog]])

    operator = prog.first()
    if not operator.listp():
        as_atom = operator.as_atom()

        if as_atom == b"mac":
            return prog.to([QUOTE_KW, [QUOTE_KW, macro_lookup]])

        for macro_pair in macro_lookup.as_iter():
            macro_name = macro_pair.first()
            if macro_name.as_atom() == as_atom:
                macro_code = macro_pair.rest().first()
                post_prog = brun(macro_code, prog.rest())
                return post_prog

        if as_atom in COMPILE_BINDINGS:
            f = COMPILE_BINDINGS[as_atom]
            post_prog = f(prog.rest())
            return post_prog.to([QUOTE_KW, post_prog])
    return None


def do_com_prog(prog, macro_lookup):
    """
    prog is an uncompiled s-expression.
    Returns an equivalent compiled s-expression by calling "exp"
    or passing through an already compiled operator.

    It will not start with "com" (or we're in recursion trouble).
    """

    expanded_prog = do_exp_prog(prog, macro_lookup)
    if expanded_prog is not None:
        return mark_expanded(expanded_prog)

    operator = prog.first()
    if not operator.listp():
        as_atom = operator.as_atom()

        if as_atom == QUOTE_KW:
            return prog

        compiled_args = prog.to([
            mark_uncompiled(_) for _ in prog.rest().as_iter()])

        if as_atom in PASS_THROUGH_OPERATORS:
            return prog.to(as_atom).cons(compiled_args)

    raise SyntaxError(
        "can't compile %s, unknown operator" %
        disassemble(prog))


def do_com(sexp, eval_f):
    prog = sexp.first()
    if not sexp.rest().nullp():
        macro_lookup = sexp.rest().first()
    else:
        macro_lookup = default_macro_lookup(eval_f)
    return do_com_prog(prog, macro_lookup)


def do_exp(sexp, eval_f):
    prog = sexp.first()
    if not sexp.rest().nullp():
        macro_lookup = sexp.rest().first()
    else:
        macro_lookup = default_macro_lookup(eval_f)
    expanded_sexp = do_exp_prog(prog, macro_lookup)
    if expanded_sexp:
        return sexp.to(expanded_sexp)
    return sexp.to(prog)
