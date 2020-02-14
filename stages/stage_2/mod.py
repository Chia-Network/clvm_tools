from clvm import KEYWORD_TO_ATOM

from clvm_tools import binutils
from clvm_tools.NodePath import NodePath

from .helpers import eval


ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]

MAIN_NAME = b""


def build_tree(items):
    """
    This function takes a Python list of items and turns it into a binary tree
    of the items, suitable for casting to an s-expression.
    """
    size = len(items)
    if size == 0:
        return []
    if size == 1:
        return items[0]
    half_size = size >> 1
    left = build_tree(items[:half_size])
    right = build_tree(items[half_size:])
    return (left, right)


def to_defconstant(_):
    return [b"defconstant", _[0], _[1]]


def to_defun(_):
    return _[1]


def new_mod(macros, functions, constants, macro_lookup):
    """
    If "mod" declares new macros, we strip out the first one, moving it to the
    lookup argument of the "com" keyword, and compiled the module free of the first
    macros.
    """
    main_local_arguments = functions[MAIN_NAME].rest().rest().first()
    uncompiled_main = functions[MAIN_NAME].rest().rest().rest().first()
    mod_sexp = (
        [b"mod", main_local_arguments] +
        [_ for _ in macros[1:]] +
        list(to_defun(_) for _ in functions.items()) +
        list(to_defconstant(_) for _ in constants.items()) +
        [uncompiled_main.as_python()])
    new_com_sexp = eval(uncompiled_main.to([b"com", [QUOTE_KW, [
        CONS_KW, macros[0], [QUOTE_KW, macro_lookup]]], [QUOTE_KW, macro_lookup]]), [ARGS_KW])
    total_sexp = eval(uncompiled_main.to([b"com", [QUOTE_KW, mod_sexp], new_com_sexp]), [ARGS_KW])
    return total_sexp


def compile_mod_stage_1(args):
    """
    stage 1: collect up names of globals (functions, constants, macros)
    """

    functions = {}
    constants = {}
    macros = []
    main_local_arguments = args.first()

    namespace = set()
    while True:
        args = args.rest()
        if args.rest().nullp():
            break
        declaration_sexp = args.first()
        op = declaration_sexp.first().as_atom()
        name = declaration_sexp.rest().first().as_atom()
        if name in namespace:
            raise SyntaxError('symbol "%s" redefined' % name.decode())
        namespace.add(name)
        if op == b"defmacro":
            macros.append(declaration_sexp)
            continue
        if op == b"defun":
            functions[name] = declaration_sexp
            continue
        if op == b"defconstant":
            constants[name] = declaration_sexp.rest().rest().first().as_atom()
            continue
        raise SyntaxError("expected defun, defmacro, or defconstant")

    uncompiled_main = args.first()

    functions[MAIN_NAME] = args.to([b"defun", MAIN_NAME, main_local_arguments, uncompiled_main])

    return functions, constants, macros


def symbol_table_for_tree(tree, root_node):
    symbol_table_programs = symbol_table_sexp(tree)

    from .bindings import run_program

    symbol_table = []
    for pair in symbol_table_programs.as_iter():
        (name, prog) = (pair.first(), pair.rest().first())
        cost, r = run_program(prog, root_node)
        symbol_table.append((name, (r, [])))
    return symbol_table_programs.to(symbol_table)


def compile_mod(args, macro_lookup, symbol_table):
    """
    Deal with the "mod" keyword.
    """
    (functions, constants, macros) = compile_mod_stage_1(args)

    # if we have any macros, restart with the macros parsed as arguments to "com"

    if macros:
        return new_mod(macros, functions, constants, macro_lookup)

    # all macros have already been moved to the "com" environment

    # build defuns table, with function names as keys

    all_constants_names = list(_ for _ in functions.keys() if _ != MAIN_NAME) + list(constants.keys())
    has_constants_tree = len(all_constants_names) > 0

    constants_tree = args.to(build_tree(all_constants_names))

    constants_root_node = args.to(NodePath().first().as_path())
    if has_constants_tree:
        args_root_node = args.to(NodePath().rest().as_path())
    else:
        args_root_node = args.to(NodePath().as_path())

    constants_symbol_table = symbol_table_for_tree(constants_tree, constants_root_node)

    from .bindings import run_program

    compiled_functions = {}
    for name, function_sexp in functions.items():
        lambda_expression = function_sexp.rest().rest()
        local_symbol_table = symbol_table_for_tree(lambda_expression.first(), args_root_node)
        all_symbols = local_symbol_table
        if not constants_symbol_table.nullp():
            all_symbols = function_sexp.to(
                local_symbol_table.as_python() + constants_symbol_table.as_python())

        expansion = lambda_expression.to(
            [b"opt", [b"com",
                      [QUOTE_KW, lambda_expression.rest().first()],
                      [QUOTE_KW, macro_lookup],
                      [QUOTE_KW, all_symbols]]])
        cost, r = run_program(expansion, args.null())
        compiled_functions[name] = r

    main_path_src = binutils.disassemble(compiled_functions[MAIN_NAME])

    if not has_constants_tree:
        main_code = "(opt (q ((c (q %s) (a)))))" % main_path_src
        return binutils.assemble(main_code)

    all_constants_lookup = dict(compiled_functions)
    all_constants_lookup.update(constants)

    all_constants_list = [all_constants_lookup[_] for _ in all_constants_names]
    all_constants_tree = args.to(build_tree(all_constants_list))

    all_constants_tree_src = binutils.disassemble(all_constants_tree)
    main_code = "(opt (q ((c (q %s) (c (q %s) (a))))))" % (main_path_src, all_constants_tree_src)
    main_sexp = binutils.assemble(main_code)
    return main_sexp


def symbol_table_sexp(sexp, so_far=[ARGS_KW]):
    """
    This function takes an s-expression sexp and returns a list (as an s-expression)
    of pairs of the form (label, path-function).

    For a given label, the path function can be called with "run_program" where args
    is the base s-expression to the root of the tree, and it will generate the
    program that gives the path to the label.
    """
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


def compile_defmacro(args, macro_lookup, symbol_table):
    """
    Deal with "defmacro" keyword.
    """
    macro_name = args.first()
    return args.to([
        b"list", macro_name, compile_mod(args.rest(), macro_lookup, symbol_table)])
