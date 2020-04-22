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
    ir_to,
    ir_first,
    ir_rest,
)

from clvm_tools.NodePath import NodePath, TOP, LEFT, RIGHT

from .mod import MAIN_NAME

SHORT_NODE_PATHS = False

CONS = ir_new(Type.SYMBOL, b"c")
QUOTE = ir_new(Type.SYMBOL, b"q")
IF = ir_new(Type.SYMBOL, b"i")

TOP_NODE = ir_new(Type.NODE, TOP.index())


def symbol_table_for_tree(tree, root_node):
    if ir_nullp(tree):
        return []

    if not ir_listp(tree):
        return [[ir_as_atom(tree), ir_new(Type.NODE, tree.to(root_node.index()))]]

    left = symbol_table_for_tree(ir_first(tree), root_node + LEFT)
    right = symbol_table_for_tree(ir_rest(tree), root_node + RIGHT)

    return left + right


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


def do_codegen(args):
    raise EvalError("unsupported", args)


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
    return None


def codegen_if(operator, args, symbol_table):
    cond_code = ir_first(args)
    args = ir_rest(args)
    true_branch = ir_first(args)
    args = ir_rest(args)
    false_branch = ir_first(args)
    code = ir_list(
        ir_list(
            CONS,
            ir_list(
                IF, cond_code, ir_list(QUOTE, true_branch), ir_list(QUOTE, false_branch)
            ),
            codegen(args.to(TOP_NODE), symbol_table),
        )
    )
    return code


def codegen_call(operator, args, symbol_table):
    # TODO
    raise EvalError("call not yet supported", operator)


def make_codegen(op):
    def codegen_special(operator, args, symbol_table):
        return ir_cons(operator, args)

    return codegen_special


CODEGEN_LOOKUP = {
    b"if": codegen_if,
    b"call": codegen_call,
    b"first": make_codegen(b"f"),
    b"rest": make_codegen(b"f"),
    b"=": make_codegen(b"="),
    b"+": make_codegen(b"+"),
    b"-": make_codegen(b"-"),
    b"*": make_codegen(b"*"),
}


def codegen_args(args, symbol_table):
    if ir_listp(args):
        return ir_cons(
            codegen(ir_first(args), symbol_table),
            codegen_args(ir_rest(args), symbol_table),
        )
    if ir_nullp(args):
        return args
    raise EvalError("bad argument list", args)


def list_to_cons(args):
    if ir_listp(args):
        return ir_list(CONS, ir_first(args), list_to_cons(ir_rest(args)))
    return ir_list(QUOTE, args)


def codegen_call_operator(operator, obj_args, symbol_table):
    # (fact N) =>
    # ((c fact[NODE] (c fact[NODE] (c N (q ())))))
    operator_code = codegen(operator, symbol_table)
    obj_args_conses = list_to_cons(obj_args)
    code = ir_list(
        ir_list(CONS, operator_code, ir_list(CONS, operator_code, obj_args_conses,),),
    )
    return code


def codegen_cons(operator, source_args, symbol_table):
    obj_args = source_args.to(codegen_args(source_args, symbol_table))
    if ir_listp(operator):
        opcode = codegen(operator, symbol_table)
    elif ir_type(operator) == Type.SYMBOL:
        op = ir_as_atom(operator)
        r = symbol_from_table(op, symbol_table)
        if r:
            return codegen_call_operator(operator, obj_args, symbol_table)
        if op not in CODEGEN_LOOKUP:
            raise EvalError("unknown operator", ir_val(operator))
        special_codegen_f = CODEGEN_LOOKUP.get(op)
        if special_codegen_f:
            return special_codegen_f(operator, obj_args, symbol_table)
        opcode = operator
    return ir_cons(opcode, obj_args)


def codegen(source_code, symbol_table):
    the_type = ir_type(source_code)

    if the_type == Type.SYMBOL:
        r = symbol_from_table(ir_as_atom(source_code), symbol_table)
        if r:
            return codegen(r, symbol_table)
        # TODO: fix this by resolving symbols
        raise EvalError("undefined symbol", ir_val(source_code))

    if the_type == Type.CONS:
        operator = ir_first(source_code)
        source_args = ir_rest(source_code)
        return codegen_cons(operator, source_args, symbol_table)

    if the_type == Type.NODE:
        if SHORT_NODE_PATHS:
            node = NodePath(ir_as_int(source_code)).index()
            return ir_new(Type.INT, node)  # source_code.to(node))
        node = NodePath(ir_as_int(source_code)).as_assembly()
        return ir_to(source_code.to(node))

    if is_quotable(the_type):
        return ir_cons(ir_new(Type.SYMBOL, b"q"), ir_cons(source_code, ir_null()))

    raise EvalError("unknown type", operator)


def iter_fnimc(fnimc):
    while ir_listp(fnimc):
        entry = ir_first(fnimc)
        name = ir_as_atom(ir_first(entry))
        entry = ir_rest(entry)
        parms_code = ir_first(entry)
        entry = ir_rest(entry)
        need_mod_context = ir_as_int(ir_first(entry))
        entry = ir_rest(entry)
        in_mod_context = ir_as_int(ir_first(entry))
        yield name, parms_code, need_mod_context, in_mod_context
        fnimc = ir_rest(fnimc)


def populate_const_tree(tree, compiled_functions):
    if ir_listp(tree):
        return ir_cons(
            populate_const_tree(ir_first(tree), compiled_functions),
            populate_const_tree(ir_rest(tree), compiled_functions),
        )
    name = ir_as_atom(tree)
    f = compiled_functions[name]
    return f


def do_codegen_mod_context(args):
    # build the const-tree (if we need one)
    const_tree_items = [_[0] for _ in iter_fnimc(args.first()) if _[0] != MAIN_NAME]

    if const_tree_items:
        const_tree = args.to(build_tree(const_tree_items))

    # compile each function (now that we know the const-tree)
    compiled_functions = {}
    for name, parms_code, need_mod_context, in_mod_context in iter_fnimc(args.first()):
        parms = ir_first(parms_code)
        code = ir_first(ir_rest(parms_code))
        if const_tree_items:
            # TODO: fix this hack where we always have a mod context
            parms = args.to(ir_cons(const_tree, parms))
        # okay, now we compile it!
        symbol_table = symbol_table_for_tree(parms, TOP)
        symbol_table = args.to(
            ir_list(*[ir_cons(ir_new(Type.SYMBOL, _[0]), _[1]) for _ in symbol_table])
        )

        assembly = codegen(code, symbol_table)
        compiled_functions[name] = assembly

    final_code = compiled_functions[MAIN_NAME]

    if const_tree_items:
        compiled_top = codegen(args.to(ir_new(Type.NODE, TOP.index())), ir_null())

        main_code = final_code
        # build const-tree
        populated_const_tree = populate_const_tree(const_tree, compiled_functions)

        augmented_const_tree = ir_list(
            CONS, ir_list(QUOTE, populated_const_tree), compiled_top,
        )

        # ((c (q MAIN_CODE) (c (q MOD-CONTEXT) (a))))

        final_code = args.to(
            ir_list(ir_list(CONS, ir_list(QUOTE, main_code), augmented_const_tree))
        )
    return 1, args.to(final_code)
