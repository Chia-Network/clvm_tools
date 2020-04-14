from clvm.EvalError import EvalError

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
    ir_as_int,
    ir_first,
    ir_rest,
)

from clvm_tools.NodePath import NodePath, LEFT, RIGHT, TOP


from clvm.runtime_001 import KEYWORD_TO_ATOM


CONS = KEYWORD_TO_ATOM["c"]
QUOTE = KEYWORD_TO_ATOM["q"]


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


def do_codegen(args):
    arg = args.first()
    source_code = ir_first(arg)
    symbol_table = ir_rest(arg)
    return 1, codegen(source_code, symbol_table)


def is_quotable(op):
    return op in (
        Type.NULL,
        Type.INT,
        Type.HEX,
        Type.QUOTES,
        Type.SINGLE_QUOTE,
        Type.DOUBLE_QUOTE,
    )


def symbol_from_table(symbol, symbol_table):
    while not ir_nullp(symbol_table):
        m = ir_first(symbol_table)
        if ir_val(ir_first(m)) == symbol:
            return ir_rest(m)
        symbol_table = ir_rest(symbol_table)
    raise EvalError("undefined symbol", symbol)


def codegen_args(args, symbol_table):
    if ir_nullp(args):
        return args.null()
    if ir_listp(args):
        return codegen(ir_first(args), symbol_table).cons(
            codegen_args(ir_rest(args), symbol_table)
        )
    return codegen(args, symbol_table)


def codegen_operator(operator, source_args, symbol_table):
    if ir_listp(operator):
        opcode = codegen(operator, symbol_table)
    elif ir_type(operator) == Type.SYMBOL:
        op = ir_as_atom(operator).decode()
        r = symbol_from_table(op, symbol_table)
        if r:
            breakpoint()
        opcode = KEYWORD_TO_ATOM.get(op)
        if opcode is None:
            raise EvalError("unknown operator", ir_val(operator))
        obj_args = codegen_args(source_args, symbol_table)
    return operator.to(opcode).cons(obj_args)


def codegen(source_code, symbol_table):

    the_type = ir_type(source_code)

    if the_type == Type.SYMBOL:
        r = symbol_from_table(ir_val(source_code), symbol_table)
        # TODO: fix this by resolving symbols
        raise EvalError("undefined symbol", ir_val(source_code))

    if the_type == Type.CONS:
        operator = ir_first(source_code)
        source_args = ir_rest(source_code)
        return codegen_operator(operator, source_args, symbol_table)

    if the_type == Type.NODE:
        node = NodePath(ir_as_int(source_code)).as_path()
        return source_code.to(node)

    if is_quotable(the_type):
        return source_code.to([QUOTE, ir_val(source_code)])

    raise EvalError("unknown type", operator)
