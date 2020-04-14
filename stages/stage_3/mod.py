from ir.reader import read_ir
from ir.writer import write_ir

from clvm.runtime_001 import KEYWORD_TO_ATOM

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


def do_compile_lambda(args):
    # (parms code)

    parms = ir_first(args.first())
    code = ir_first(ir_rest(args.first()))

    # create lookup of missing symbols to parms

    symbol_table = dict(symbol_table_for_tree(parms, TOP))

    # substitute symbols
    r = sub_symbols(code, symbol_table)
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
