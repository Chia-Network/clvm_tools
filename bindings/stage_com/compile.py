from clvm import KEYWORD_TO_ATOM, to_sexp_f
from opacity.binutils import disassemble


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


PASS_THROUGH_OPERATORS = set(
    KEYWORD_TO_ATOM[_] for _ in
    "e a i c f r l x = sha256 + - * . wrap unwrap point_add pubkey_for_exp".split()
)

PASS_THROUGH_OPERATORS.update([b"macro_lookup"])


def compile_list(args):
    if not args.listp() or args.nullp():
        return to_sexp_f([QUOTE_KW, args])

    return to_sexp_f([
        CONS_KW,
        args.first(),
        compile_list(args.rest())])


def compile_function(args):
    return to_sexp_f([QUOTE_KW, args.first()])


COMPILE_BINDINGS = {
    b"list": compile_list,
    b"function": compile_function,
    # b"lambda_op": compile_lambda_op,
}


def do_compile_sexp(sexp, eval_f):
    # quote atoms
    if sexp.nullp() or not sexp.listp():
        return to_sexp_f([QUOTE_KW, sexp])

    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return sexp

        if as_atom == b"macro_lookup":
            return sexp

        macro_lookup = eval_f(eval_f, sexp.to([b"macro_lookup"]), sexp.null())
        for macro_pair in macro_lookup.as_iter():
            macro_name = macro_pair.first()
            if macro_name.as_atom() == as_atom:
                breakpoint()
                macro_code = macro_pair.rest().first()
                sexp = eval_f(eval_f, macro_code, sexp.rest())
                return do_compile_sexp(sexp, eval_f)

        remaining_args = to_sexp_f([
            do_compile_sexp(
                _, eval_f) for _ in sexp.rest().as_iter()])

        if as_atom == b"compile_op":
            if remaining_args.first().first().as_atom() == QUOTE_KW:
                const_sexp = remaining_args.first().rest().first()
                compiled_sexp = do_compile_sexp(const_sexp, eval_f)
                return to_sexp_f([QUOTE_KW, compiled_sexp])
            return to_sexp_f(as_atom).cons(remaining_args)

        if as_atom in PASS_THROUGH_OPERATORS:
            return to_sexp_f(as_atom).cons(remaining_args)

        if as_atom in COMPILE_BINDINGS:
            f = COMPILE_BINDINGS[as_atom]
            return do_compile_sexp(f(remaining_args), eval_f)

    raise SyntaxError(
        "can't compile %s, unknown operator" %
        disassemble(sexp))


def do_compile_op(sexp, eval_f):
    return do_compile_sexp(sexp.first(), eval_f)
