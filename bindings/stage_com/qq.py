from clvm import KEYWORD_TO_ATOM, to_sexp_f


QUOTE_KW = KEYWORD_TO_ATOM["q"]


def compile_qq_sexp(sexp, eval_f):
    if sexp.nullp() or not sexp.listp():
        return to_sexp_f([QUOTE_KW, sexp])

    operator = sexp.first()
    if operator.as_atom() == b"unquote":
        return sexp.rest().first()

    next_sexp = sexp.to([b"compile_op", [QUOTE_KW, [b"list"] + [
        compile_qq_sexp(_, eval_f) for _ in sexp.as_iter()]]])
    return eval_f(eval_f, next_sexp, next_sexp.null())


def compile_qq_op(args, eval_f):
    qq_sexp = eval_f(eval_f, args.first(), args.null())
    return compile_qq_sexp(qq_sexp, eval_f)
