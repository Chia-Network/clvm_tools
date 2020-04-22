def wi(ir): from ir.writer import write_ir; from clvm import to_sexp_f; print(write_ir(to_sexp_f(ir)))


def symbol_table_for_tree(tree, root_node):
    if ir_nullp(tree):
        return []

    if not ir_listp(tree):
        return [[ir_as_atom(tree), ir_new(Type.NODE, tree.to(root_node.index()))]]

    left = symbol_table_for_tree(ir_first(tree), root_node + LEFT)
    right = symbol_table_for_tree(ir_rest(tree), root_node + RIGHT)

    return left + right



def dict_to_ir_lookup(d):
    ir_sexp = ir_null()
    for k, v in d.items():
        ir_sexp = ir_cons(ir_cons(ir_new(Type.SYMBOL, k), v), ir_sexp)
    return ir_sexp


def ir_lookup_to_dict(ir_sexp):
    d = {}
    while ir_listp(ir_sexp):
        kv = ir_first(ir_sexp)
        k = ir_first(kv)
        v = ir_rest(kv)
        d[ir_as_atom(k)] = v
    return d



def from_symbol_table(symbol_table, symbol):
    while not ir_nullp(symbol_table):
        if symbol == ir_first(ir_first(symbol_table)):
            return ir_rest(ir_first(symbol_table))
        symbol_table = ir_rest(symbol_table)
    return None


def find_symbols_used(code, symbol_table, acc):
    """
    Return a list of all symbols used, recursively, each symbols listed
    at most two times.
    """
    if ir_listp(code):
        return find_symbols_used(
            ir_first(code), symbol_table, find_symbols_used(
                ir_rest(code), symbol_table, acc))

    if ir_type(code) == Type.SYMBOL:
        symbol = ir_val(code)
        acc = [code] + acc
        subcode = from_symbol_table(symbol_table, symbol)
        if subcode and symbol not in [ir_val(_) for _ in acc[1:]]:
            acc = find_symbols_used(subcode, symbol_table, acc)

    return acc


def find_repeated(symbols):
    names = [ir_as_atom(_) for _ in symbols]
    d = {_: 0 for _ in names}
    for _ in names:
        d[_] += 1
    return [_ for _ in d.keys() if d[_] > 1]


