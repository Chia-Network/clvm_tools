from ir.writer import write_ir as wi


from clvm import run_program as original_run_program

from clvm.runtime_001 import OPERATOR_LOOKUP as ORIGINAL_OPERATOR_LOOKUP
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
    ir_symbol,
    ir_as_symbol,
    ir_iter,
)

from clvm_tools.binutils import assemble_from_ir

from clvm_tools.NodePath import LEFT, RIGHT, TOP


CONS = ir_new(Type.OPERATOR, b"c")
QUOTE = ir_new(Type.OPERATOR, b"q")


OPERATOR_LOOKUP = dict(ORIGINAL_OPERATOR_LOOKUP)


def run_program(*args, **kwargs):
    return original_run_program(*args, **kwargs, operator_lookup=OPERATOR_LOOKUP)


def do_com(args):
    return 1, args


def do_assemble(args):
    r = assemble_from_ir(args.first())
    return 1, ir_new(Type.CODE, r)


def ir_flatten(ir_sexp):
    if ir_listp(ir_sexp):
        return ir_flatten(ir_first(ir_sexp)) + ir_flatten(ir_rest(ir_sexp))
    if ir_type(ir_sexp) == Type.SYMBOL:
        return [ir_val(ir_sexp).as_atom()]
    return []


def do_compile_lambda(args):
    # (parms code all_symbols_from_parms all_symbols_from_code)

    parms = args.first()
    code = args.rest().first()
    symbols_from_parms = ir_flatten(args.rest().rest().first())
    symbols_from_code = ir_flatten(args.rest().rest().rest().first())

    # find missing symbols, rewrite bind code, adjust var look-up

    built_in_ops = [_.encode() for _ in KEYWORD_TO_ATOM.keys()]

    missing_symbols = sorted(
        set(symbols_from_code).difference(symbols_from_parms).difference(built_in_ops)
    )

    # create lookup of missing symbols to parms

    new_parms = parms
    if missing_symbols:
        breakpoint()
        missing_symbol_tree = build_tree(missing_symbols)
        missing_symbol_code = build_tree_program(missing_symbols)
        new_parms = parms.to(ir_cons(missing_symbol_tree, parms))
        # new code looks like this
        # code = "(qq (c (unquote CODE) (c (unquote MISSING_SYMBOL_CODE) (a))))"
        NODE_0 = ir_new(Type.NODE, 0)
        new_args = parms.to(ir_list(CONS, missing_symbol_code, NODE_0))

    symbol_table = dict(symbol_table_for_tree(new_parms, TOP))

    # substitute symbols
    r = sub_symbols(code, symbol_table)
    if missing_symbols:
        r = parms.to(ir_list(CONS, ir_list(QUOTE, r), new_args))
    return 1, r


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


def build_tree(items):
    """
    This function takes a Python list of items and turns it into a binary tree
    of the items, suitable for casting to an s-expression.
    """
    size = len(items)
    if size == 0:
        return []
    if size == 1:
        return ir_new(Type.SYMBOL, items[0])
    half_size = size >> 1
    left = build_tree(items[:half_size])
    right = build_tree(items[half_size:])
    return ir_cons(left, right)


def build_tree_program(items):
    """
    This function takes a Python list of items and turns it into a program that
    builds a binary tree of the items, suitable for casting to an s-expression.
    """
    size = len(items)
    if size == 1:
        return ir_new(Type.SYMBOL, items[0])
    half_size = size >> 1
    left = build_tree_program(items[:half_size])
    right = build_tree_program(items[half_size:])
    return ir_list(CONS, left, right)


def symbol_table_for_tree(tree, root_node):
    if ir_nullp(tree):
        return []

    if not ir_listp(tree):
        return [[ir_as_atom(tree), ir_new(Type.NODE, tree.to(root_node.index()))]]

    left = symbol_table_for_tree(ir_first(tree), root_node + LEFT)
    right = symbol_table_for_tree(ir_rest(tree), root_node + RIGHT)

    return left + right


OPERATOR_LOOKUP[b"com"] = do_com
OPERATOR_LOOKUP[b"_assemble"] = do_assemble
OPERATOR_LOOKUP[b"_compile_lambda"] = do_compile_lambda
