from clvm import KEYWORD_TO_ATOM

from .helpers import brun


# (lambda x (* x x)) => (quote (* (a) (a)))
# lambda_op
# (symbol_replace sexp symbol_table)
# (symbol_table sexp) => symbol_table

ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]
EVAL_KW = KEYWORD_TO_ATOM["e"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


def symbol_table_sexp(sexp, so_far=[ARGS_KW]):
    if sexp.nullp():
        return sexp

    if not sexp.listp():
        return sexp.to([[sexp, so_far]])

    r = []
    for pair in symbol_table_sexp(sexp.first(), [
            CONS_KW, [QUOTE_KW, FIRST_KW], [
                CONS_KW, so_far, [QUOTE_KW, []]]]).as_iter():
        _ = pair.first()
        node = pair.rest().first()
        r.append(_.to([_, node]))
    for pair in symbol_table_sexp(sexp.rest(), [
            CONS_KW, [QUOTE_KW, REST_KW], [
                CONS_KW, so_far, [QUOTE_KW, []]]]).as_iter():
        _ = pair.first()
        node = pair.rest().first()
        r.append(_.to([_, node]))

    return sexp.to(r)


def symbol_replace(sexp, symbol_table, root_node):
    if sexp.nullp():
        return sexp

    if not sexp.listp():
        for pair in symbol_table.as_iter():
            symbol = pair.first().as_atom()
            if symbol == sexp.as_atom():
                prog = pair.rest().first()
                return brun(prog, root_node)
        return sexp

    return sexp.to([b"list", sexp.first()] + [
        symbol_replace(_, symbol_table, root_node)
        for _ in sexp.rest().as_iter()])


def compile_lambda(args, macro_lookup):
    symbol_table = symbol_table_sexp(args.first())
    root_node = args.to([ARGS_KW])
    expansion = symbol_replace(
        args.rest().first(), symbol_table, root_node)
    r = args.to([
        EVAL_KW, [b"qq", [b"com", [
            QUOTE_KW, [b"function", [b"unquote", expansion]]], [QUOTE_KW, macro_lookup]]], [ARGS_KW]])
    r = args.to([EVAL_KW, r, [ARGS_KW]])
    return r


def compile_defmacro(args, macro_lookup):
    macro_name = args.first()
    return args.to([
        b"list", macro_name, compile_lambda(args.rest(), macro_lookup)])
