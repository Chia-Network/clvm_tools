from clvm import KEYWORD_TO_ATOM

from clvm_tools import binutils

from .helpers import eval


ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]

MAIN_NAME = b""


def symbol_replace(sexp, symbol_table, root_node):
    """
    Look for unresolved symbols in the symbol table and replace them with paths.
    """
    if sexp.nullp():
        return sexp

    if not sexp.listp():
        for pair in symbol_table.as_iter():
            symbol = pair.first().as_atom()
            if symbol == sexp.as_atom():
                prog = pair.rest().first()
                return eval(prog.to([QUOTE_KW, prog]), [QUOTE_KW, root_node])
        return sexp

    return sexp.to([b"list"] + [
        symbol_replace(_, symbol_table, root_node)
        for _ in sexp.as_iter()])


def load_declaration(lambda_expression, root_node, macro_lookup):
    """
    Parse and compile an anonymous function declaration s-expression.

    This takes a defun or defmacro declaration (with the keyword stripped away)
    and substitutes all references to local arguments with a drill-down
    argument path like (f (r (... root_node))).
    """
    local_symbol_table = symbol_table_sexp(lambda_expression.first())
    expansion = lambda_expression.to([b"com", [QUOTE_KW, symbol_replace(
        lambda_expression.rest().first(), local_symbol_table, root_node)]])
    from .bindings import run_program
    null = expansion.null()
    cost, r = run_program(expansion, null)
    return r


def imp_to_defmacro(name, position_sexp):
    """
    This function takes a symbol name (which represents a function)
    and defines a macro to replace it with an invocation in the given
    position. Then it's added to the macro region and compiled.
    """
    position = binutils.disassemble(position_sexp)
    body_src = (
        "(defmacro %s ARGS (qq ((c %s (c (f (a))"
        " (unquote (c list ARGS)))))))" % (
            name.decode("utf8"), position))
    body_sexp = binutils.assemble(body_src)
    return body_sexp


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


def build_positions(function_items, to_sexp_f):
    """
    Take a list of pairs of (name, function) and build a tree of them.
    The name is a byte label. The function is an s-expression with local arguments already
    substituted out (but globals not).

    Return a dictionary and a list.

    The dictionary is a lookup of name to position in the tree (as an s-expression path).
    The list contains s-expressions implementing the functions.
    """

    null = to_sexp_f([])

    function_pairs = list(function_items)
    tree = to_sexp_f(build_tree([_[0] for _ in function_pairs]))
    from .bindings import run_program
    symbol_table = symbol_table_sexp(tree)
    root_node = to_sexp_f([FIRST_KW, [ARGS_KW]])
    d = {}
    for pair in symbol_table.as_iter():
        name = pair.first().as_atom()
        prog = pair.rest().first()
        cost, position = run_program(prog, root_node)
        d[name] = position

    expanded_imps = []
    for _ in function_pairs:
        cost, r = run_program(_[1], null)
        expanded_imps.append(r)
    return d, expanded_imps


def build_mac_wrapper(macros, macro_lookup):
    """
    Given a set of new macros and the existing macro lookup table, build a
    new macro lookup table that includes both the existing ones and the
    new ones.
    """
    mlt = "(q %s)" % binutils.disassemble(macro_lookup)
    text = mlt
    for _ in macros:
        src = binutils.disassemble(_)
        text = "(c %s %s)" % (src, text)
    wrapper_src = "((c (com (q %s) %s) (a)))" % (text, mlt)
    wrapper_sexp = binutils.assemble(wrapper_src)
    return wrapper_sexp


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


def build_function_table(functions, root_node, macro_lookup):
    """
    Take the function table and build:

    - pre_substituted_imps: the implementation with local arguments replace with node paths
    """

    defuns = {}
    for function_name, function in functions.items():
        imp = load_declaration(function.rest().rest(), root_node, macro_lookup)
        defuns[function_name] = imp
    position_lookup, pre_substituted_imps = build_positions(
        defuns.items(), root_node.to)

    return pre_substituted_imps, position_lookup


def build_function_compilation_macros(position_lookup):
    """
    Turn the position_lookup dictionary into a list of function_compilation_macros.
    These are macros to add to the space that will replace function operators
    with invocations of that function by path.
    """
    function_compilation_macros = []
    for name, position_sexp in position_lookup.items():
        function_compilation_macros.append(imp_to_defmacro(name, position_sexp))
    return function_compilation_macros


def compile_mod(args, macro_lookup, symbol_table):
    """
    Deal with the "mod" keyword.
    """
    (functions, constants, macros) = compile_mod_stage_1(args)

    null = args.null()

    # if we have any macros, restart with the macros parsed as arguments to "com"

    if macros:
        return new_mod(macros, functions, constants, macro_lookup)

    # all macros have already been moved to the "com" environment

    root_node = args.to([ARGS_KW])
    if len(functions) > 1:
        root_node = args.to([REST_KW, root_node])

    main_declaration = functions[MAIN_NAME].rest().rest()
    del functions[MAIN_NAME]

    # build defuns table, with function names as keys

    all_constants = list(functions.keys()) + list(constants.keys())
    if len(all_constants) >= 1:
        return compile_mod_alt(args, macro_lookup, symbol_table)

    pre_substituted_imps, position_lookup = build_function_table(functions, root_node, macro_lookup)
    function_compilation_macros = build_function_compilation_macros(position_lookup)

    macro_wrapper = build_mac_wrapper(function_compilation_macros, macro_lookup)

    main_sexp = load_declaration(main_declaration, root_node, macro_lookup)
    main_src = binutils.disassemble(main_sexp)
    macro_wrapper_src = binutils.disassemble(macro_wrapper)

    from .bindings import run_program

    compiled_main_src = "(opt (com %s %s))" % (main_src, macro_wrapper_src)
    cost, expanded_main = run_program(binutils.assemble(compiled_main_src), null)

    if not functions:
        # no functions, just macros
        return expanded_main.to([QUOTE_KW, expanded_main])

    imps = []
    for _ in pre_substituted_imps:
        sub_sexp = _.to([b"opt", [b"com", [QUOTE_KW, _], macro_wrapper]])
        cost, r = run_program(sub_sexp, null)
        imps.append(r)

    imps_tree = args.to(build_tree(imps))
    imps_tree_src = binutils.disassemble(imps_tree)
    expanded_main_src = binutils.disassemble(expanded_main)
    entry_src = "(opt (q ((c (q %s) (c (q %s) (a)))))))" % (
        expanded_main_src, imps_tree_src)

    return binutils.assemble(entry_src)


def symbol_table_for_tree(tree, root_node):
    symbol_table_programs = symbol_table_sexp(tree)

    from .bindings import run_program

    symbol_table = []
    for pair in symbol_table_programs.as_iter():
        (name, prog) = (pair.first(), pair.rest().first())
        cost, r = run_program(prog, root_node)
        symbol_table.append((name, (r, [])))
    return symbol_table_programs.to(symbol_table)


def compile_mod_alt(args, macro_lookup, symbol_table):
    """
    Deal with the "mod" keyword.
    """
    (functions, constants, macros) = compile_mod_stage_1(args)

    # if we have any macros, restart with the macros parsed as arguments to "com"

    if macros:
        return new_mod(macros, functions, constants, macro_lookup)

    # all macros have already been moved to the "com" environment

    constants_root_node = args.to([FIRST_KW, [ARGS_KW]])
    args_root_node = args.to([REST_KW, [ARGS_KW]])

    # build defuns table, with function names as keys

    all_constants_names = list(_ for _ in functions.keys() if _ != MAIN_NAME) + list(constants.keys())
    constants_tree = args.to(build_tree(all_constants_names))
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

    all_constants_lookup = dict(compiled_functions)
    all_constants_lookup.update(constants)

    all_constants_list = [all_constants_lookup[_] for _ in all_constants_names]
    all_constants_tree = args.to(build_tree(all_constants_list))

    main_path_src = binutils.disassemble(compiled_functions[MAIN_NAME])
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
