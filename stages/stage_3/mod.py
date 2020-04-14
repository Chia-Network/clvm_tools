from ir.Type import Type
from ir.utils import (
    ir_new,
    ir_cons,
    ir_null,
    ir_type,
    ir_list,
    ir_offset,
    ir_val,
    ir_nullp,
    ir_listp,
    ir_as_sexp,
    ir_is_atom,
    ir_as_atom,
    ir_first,
    ir_rest,
)

from clvm_tools.NodePath import LEFT, RIGHT, TOP

MAIN_NAME = b""


def parse_mod_sexp(declaration_sexp, namespace, functions, constants, macros):
    op = ir_as_atom(ir_first(declaration_sexp))
    name = ir_as_atom(ir_first(ir_rest(declaration_sexp)))
    if name in namespace:
        raise SyntaxError('symbol "%s" redefined' % name.decode())
    namespace.add(name)
    if op == b"defmacro":
        macros.append(declaration_sexp)
    elif op == b"defun":
        functions[name] = ir_rest(ir_rest(declaration_sexp))
    elif op == b"defconstant":
        # TODO: this probably doesn't work right
        constants[name] = ir_as_atom(ir_first(ir_rest(ir_rest(declaration_sexp))))
    else:
        raise SyntaxError("expected defun, defmacro, or defconstant")


def compile_mod_stage_1(args):
    """
    stage 1: collect up names of globals (functions, constants, macros)
    """

    functions = {}
    constants = {}
    macros = []
    main_local_arguments = ir_first(args)

    namespace = set()
    while True:
        args = ir_rest(args)
        if ir_nullp(ir_rest(args)):
            break
        parse_mod_sexp(ir_first(args), namespace, functions, constants, macros)

    uncompiled_main = ir_first(args)

    functions[MAIN_NAME] = ir_cons(main_local_arguments, uncompiled_main)

    return functions, constants, macros


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


def do_compile_lambda(args):
    """
    args = (parms, code)
    returns (compiled_code, symbol_table)
    """

    #breakpoint()
    (functions, constants, macros) = compile_mod_stage_1(args.first())
    # for now, ignore constants and macros

    compiled = {}
    for name, parms_code in functions.items():
        parms = ir_first(parms_code)
        code = ir_rest(parms_code)

        # create lookup of missing symbols to parms

        symbol_table = dict(symbol_table_for_tree(parms, TOP))

        # substitute symbols
        compiled[name] = sub_symbols(code, symbol_table)

    symbol_table = ir_null()
    for k, v in compiled.items():
        symbol_table = ir_cons((ir_cons(k, v)), symbol_table)

    symbols = find_symbols_used(compiled[MAIN_NAME], symbol_table, [])

    repeated_symbols = find_repeated(symbols)
    repeated_symbols = args.to(ir_list(*[ir_new(Type.SYMBOL, _) for _ in find_repeated(symbols)]))

    breakpoint()
    r = ir_list(compiled[MAIN_NAME], repeated_symbols)
    return 1, parms.to(r)


def sub_symbols(ir_sexp, symbol_table):
    if ir_listp(ir_sexp):
        return ir_cons(
            sub_symbols(ir_first(ir_sexp), symbol_table),
            sub_symbols(ir_rest(ir_sexp), symbol_table),
        )

    if ir_type(ir_sexp) == Type.SYMBOL:
        v = symbol_table.get(ir_as_atom(ir_sexp))
        if v:
            return v

    return ir_sexp


def symbol_table_for_tree(tree, root_node):
    if ir_nullp(tree):
        return []

    if not ir_listp(tree):
        return [[ir_as_atom(tree), ir_new(Type.NODE, tree.to(root_node.index()))]]

    left = symbol_table_for_tree(ir_first(tree), root_node + LEFT)
    right = symbol_table_for_tree(ir_rest(tree), root_node + RIGHT)

    return left + right
