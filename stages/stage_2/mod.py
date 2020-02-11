from clvm import KEYWORD_TO_ATOM

from clvm_tools import binutils

from .helpers import eval


ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


def load_declaration(args, root_node):
    """
    Parse and compile an anonymous function declaration s-expression.

    This takes a defun or defmacro declaration (with the keyword stripped away)
    and substitutes all references to local arguments with a drill-down
    argument path like (f (r (... root_node))).
    """
    local_symbol_table = symbol_table_sexp(args.first())
    expansion = args.to([b"com", [QUOTE_KW, symbol_replace(
        args.rest().first(), local_symbol_table, root_node)]])
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
            name, position))
    body_sexp = binutils.assemble(body_src)
    return body_sexp


def build_tree(items):
    """
    This function takes a Python list of items and turns it into a binary tree
    of the items, suitable for casting to an s-expression.
    """
    size = len(items)
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


def new_mod(
        macros, functions, constants, main_symbols, uncompiled_main, macro_lookup):
    """
    If "mod" declares new macros, we strip them out and simply start again, moving the new
    macros to the lookup argument of the "com" keyword, and compiled the module free of
    macros.
    """
    mod_sexp = (
        [b"mod", main_symbols] +
        [_ for _ in macros[1:]] +
        functions + constants +
        [uncompiled_main.as_python()])
    new_com_sexp = eval(uncompiled_main.to([b"com", [QUOTE_KW, [
        CONS_KW, macros[0], [QUOTE_KW, macro_lookup]]], [QUOTE_KW, macro_lookup]]), [ARGS_KW])
    total_sexp = eval(uncompiled_main.to([b"com", [QUOTE_KW, mod_sexp], new_com_sexp]), [ARGS_KW])
    return total_sexp


def compile_mod(args, macro_lookup):
    """
    Deal with the "mod" keyword.
    """
    null = args.null()

    functions = []
    constants = []
    macros = []
    main_symbols = args.first()

    # stage 1: collect up names of globals (functions, constants, macros)

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
            functions.append(declaration_sexp)
            continue
        if op == b"defconstant":
            constants.append(declaration_sexp)
            continue
        raise SyntaxError("expected defun, defmacro, or defconstant")

    if constants:
        raise SyntaxError("defconstant not yet supported")

    uncompiled_main = args.first()

    # if we have any macros, restart with the macros parsed as arguments to "com"

    if macros:
        return new_mod(
            macros, functions, constants, main_symbols,
            uncompiled_main, macro_lookup)

    root_node = args.to([ARGS_KW])
    if functions:
        root_node = args.to([REST_KW, root_node])

    # build defuns table, with function names as keys

    defuns = {}
    for function in functions:
        declaration_sexp = function.rest()
        function_name = declaration_sexp.first().as_atom()
        declaration_sexp = declaration_sexp.rest()
        imp = load_declaration(declaration_sexp, root_node)
        defuns[function_name] = imp

    main_lambda = args.to([main_symbols, uncompiled_main])
    main_sexp = load_declaration(main_lambda, root_node)

    if defuns:
        position_lookup, pre_subtituted_imps = build_positions(
            defuns.items(), args.to)

        # add defun macros
        for name, position_sexp in position_lookup.items():
            macros.append(imp_to_defmacro(
                name.decode("utf8"), position_sexp))

    macro_wrapper = build_mac_wrapper(macros, macro_lookup)

    main_src = binutils.disassemble(main_sexp)
    macro_wrapper_src = binutils.disassemble(macro_wrapper)

    from .bindings import run_program

    compiled_main_src = "(opt (com %s %s))" % (main_src, macro_wrapper_src)
    cost, expanded_main = run_program(binutils.assemble(compiled_main_src), null)

    if not defuns:
        # no functions, just macros
        return expanded_main.to([QUOTE_KW, expanded_main])

    imps = []
    for _ in pre_subtituted_imps:
        sub_sexp = _.to([b"opt", [b"com", [QUOTE_KW, _], macro_wrapper]])
        cost, r = run_program(sub_sexp, null)
        imps.append(r)
    imps_sexp = args.to(imps)

    imps_tree = imps_sexp.to(build_tree(imps_sexp.as_python()))
    imps_tree_src = binutils.disassemble(imps_tree)
    expanded_main_src = binutils.disassemble(expanded_main)
    entry_src = "(opt (q ((c (q %s) (c (q %s) (a)))))))" % (
        expanded_main_src, imps_tree_src)

    return binutils.assemble(entry_src)


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


def compile_defmacro(args, macro_lookup):
    """
    Deal with "defmacro" keyword.
    """
    macro_name = args.first()
    return args.to([
        b"list", macro_name, compile_mod(args.rest(), macro_lookup)])
