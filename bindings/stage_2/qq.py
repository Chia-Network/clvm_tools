from clvm import KEYWORD_TO_ATOM, to_sexp_f


QUOTE_KW = KEYWORD_TO_ATOM["q"]


def has_unquote(sexp):
    if sexp.listp() and not sexp.nullp():
        operator = sexp.first()
        if operator.as_atom() == b"unquote":
            return True
        return any(has_unquote(_) for _ in sexp.rest().as_iter())
    return False


def compile_qq_sexp(sexp):
    if sexp.nullp() or not sexp.listp():
        return to_sexp_f([QUOTE_KW, sexp])

    operator = sexp.first()
    if operator.as_atom() == b"unquote":
        return sexp.rest().first()

    if has_unquote(sexp):
        return sexp.to([b"list"] + [
            compile_qq_sexp(_) for _ in sexp.as_iter()])
    return sexp.to([QUOTE_KW, sexp])
