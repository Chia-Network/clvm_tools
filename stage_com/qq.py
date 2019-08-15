from clvm import KEYWORD_TO_ATOM, to_sexp_f


QUOTE_KW = KEYWORD_TO_ATOM["q"]


def compile_qq_sexp(sexp):
    if sexp.nullp() or not sexp.listp():
        return to_sexp_f([QUOTE_KW, sexp])

    operator = sexp.first()
    if operator.as_atom() == b"unquote":
        return sexp.rest().first()

    next_sexp = sexp.to([b"list"] + [
        compile_qq_sexp(_) for _ in sexp.as_iter()])
    return next_sexp


def compile_qq_op(args):
    qq_sexp = eval_f(eval_f, args.first(), args.null())
    return compile_qq_sexp(qq_sexp)
