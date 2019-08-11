from clvm import KEYWORD_TO_ATOM, to_sexp_f
from opacity.binutils import disassemble

from .lambda_ import compile_lambda_op
from .qq import compile_qq_op


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


PASS_THROUGH_OPERATORS = set(
    KEYWORD_TO_ATOM[_] for _ in
    "e a i c f r l x = sha256 + - * . wrap unwrap point_add pubkey_for_exp".split()
)


def compile_list(args, eval_f):
    if not args.listp() or args.nullp():
        return to_sexp_f([QUOTE_KW, args])

    return to_sexp_f([
        CONS_KW,
        args.first(),
        compile_list(args.rest(), eval_f)])


def compile_function(args, eval_f):
    return to_sexp_f([QUOTE_KW, args.first()])


COMPILE_BINDINGS = {
    b"list": compile_list,
    b"function": compile_function,
    b"lambda_op": compile_lambda_op,
}


def do_compile_sexp(sexp):
    # quote atoms
    if sexp.nullp() or not sexp.listp():
        return to_sexp_f([QUOTE_KW, sexp])

    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return sexp

        remaining_args = to_sexp_f([
            do_compile_sexp(_) for _ in sexp.rest().as_iter()])

        if as_atom == b"compile_op":
            if remaining_args.first().first().as_atom() == QUOTE_KW:
                const_sexp = remaining_args.first().rest().first()
                compiled_sexp = do_compile_sexp(const_sexp)
                return to_sexp_f([QUOTE_KW, compiled_sexp])
            return to_sexp_f(as_atom).cons(remaining_args)

        if as_atom in PASS_THROUGH_OPERATORS:
            return to_sexp_f(as_atom).cons(remaining_args)

        if as_atom in COMPILE_BINDINGS:
            f = COMPILE_BINDINGS[as_atom]
            return do_compile_sexp(f(remaining_args))

    raise SyntaxError(
        "can't compile %s, unknown operator" %
        disassemble(sexp))


def do_compile_op(sexp):
    return do_compile_sexp(sexp.first())
