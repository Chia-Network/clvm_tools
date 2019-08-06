from clvm import KEYWORD_TO_ATOM


# (lambda x (* x x)) => (quote (* (a) (a)))
# lambda_op
# (symbol_replace sexp symbol_table)
# (symbol_table sexp) => symbol_table

ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]


def symbol_table_sexp(sexp, so_far=[ARGS_KW]):
    if sexp.nullp():
        return sexp

    if not sexp.listp():
        return sexp.to([[sexp, so_far]])

    r = []
    for pair in symbol_table_sexp(sexp.first(), [FIRST_KW, so_far]).as_iter():
        _ = pair.first()
        node = pair.rest().first()
        r.append(_.to([_, node]))
    for pair in symbol_table_sexp(sexp.rest(), [REST_KW, so_far]).as_iter():
        _ = pair.first()
        node = pair.rest().first()
        r.append(_.to([_, node]))

    return sexp.to(r)


def symbol_replace(sexp, symbol_table):
    if sexp.nullp():
        return sexp

    if not sexp.listp():
        for pair in symbol_table.as_iter():
            symbol = pair.first().as_atom()
            if symbol == sexp.as_atom():
                return pair.rest().first()
        return sexp

    return sexp.to([sexp.first()] + [
        symbol_replace(_, symbol_table) for _ in sexp.rest().as_iter()])


def do_lambda_op(args, eval_f):
    symbol_table = symbol_table_sexp(args.first())
    expansion = symbol_replace(args.rest().first(), symbol_table)
    return expansion
