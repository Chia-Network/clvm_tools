from clvm import KEYWORD_TO_ATOM

from opacity import binutils

from .lambda_ import symbol_table_sexp, symbol_replace


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


"""
(mod (N)
    (defun fact K (if (= K 1) 1 (* K (fact (- K 1)))))
    (defun next_fib (n0 n1) (list n1 (+ n0 n1)))
    (defun fib2 N (if (= N 0) (q (0 1)) (next_fib (fib2 (- N 1)))))
    (defun fib N (first (fib2 N)))
    (+ (fib N) (fact N))
)
"""


"""
(mod (A B)
    (defun square (N) (* N N))
    (defun hyp (A B) (+ (square A) (square B)))
    (hyp A B)
)
"""


def load_declaration(args, root_node):
    symbol_table = symbol_table_sexp(args.first())
    expansion = args.to([b"com", [QUOTE_KW, symbol_replace(
        args.rest().first(), symbol_table, root_node)]])
    from .bindings import EVAL_F
    null = expansion.null()
    return EVAL_F(EVAL_F, expansion, null)


def imp_to_defmacro(name, position):
    body_src = (
        "(defmacro %s ARGS (qq (e %s (c (f (a))"
        " (unquote (c list ARGS))))))" % (
            name, position))
    body_sexp = binutils.assemble(body_src)
    return body_sexp


def build_tree_prog(items):
    size = len(items)
    if size == 1:
        return items[0]
    half_size = size >> 1
    left = build_tree_prog(items[:half_size])
    right = build_tree_prog(items[half_size:])
    return [CONS_KW, left, right]


def build_positions(function_items, to_sexp_f):

    null = to_sexp_f([])

    function_pairs = list(function_items)
    tree_prog = to_sexp_f(build_tree_prog([[
        QUOTE_KW, _[0]] for _ in function_pairs]))
    from .bindings import EVAL_F
    tree = EVAL_F(EVAL_F, tree_prog, null)
    symbol_table = symbol_table_sexp(tree)
    root_node = to_sexp_f([FIRST_KW, [ARGS_KW]])
    d = {}
    for pair in symbol_table.as_iter():
        name = pair.first().as_atom()
        prog = pair.rest().first()
        position = EVAL_F(EVAL_F, prog, root_node)
        d[name] = position

    expanded_imps = [EVAL_F(EVAL_F, _[1], null) for _ in function_pairs]
    return d, expanded_imps


def build_mac_wrapper(macros, macro_lookup):
    mlt = "(q %s)" % binutils.disassemble(macro_lookup)
    text = mlt
    for _ in macros:
        text = "(c %s %s)" % (_, text)
    wrapper_src = "(e (com (q %s) %s) (a))" % (text, mlt)
    wrapper_sexp = binutils.assemble(wrapper_src)
    return wrapper_sexp


def new_mod(
        macros, functions, main_symbols, uncompiled_main, macro_lookup):
    mod_sexp = (
        [b"mod", main_symbols] +
        [_ for _ in macros[1:]] +
        functions +
        [uncompiled_main.as_python()])
    new_com_sexp = ([EVAL_KW, [b"com", [QUOTE_KW, [
        CONS_KW, macros[0], [QUOTE_KW, macro_lookup]]], [QUOTE_KW, macro_lookup]], [ARGS_KW]])
    total_sexp = uncompiled_main.to([EVAL_KW, [b"com", [QUOTE_KW, mod_sexp], new_com_sexp], [ARGS_KW]])
    return total_sexp


def compile_mod(args, macro_lookup):
    null = args.null()

    functions = []
    macros = []
    main_symbols = args.first()

    while True:
        args = args.rest()
        if args.rest().nullp():
            break
        declaration_sexp = args.first()
        op = declaration_sexp.first().as_atom()
        if op == b"defmacro":
            macros.append(declaration_sexp)
            continue
        if op == b"defun":
            functions.append(declaration_sexp)
            continue
        raise SyntaxError("expected defun or defmacro")

    uncompiled_main = args.first()

    if macros:
        return new_mod(
            macros, functions, main_symbols,
            uncompiled_main, macro_lookup)

    root_node = args.to([ARGS_KW])
    if functions:
        root_node = args.to([REST_KW, root_node])

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
        for name, position in position_lookup.items():
            macros.append(imp_to_defmacro(name.decode("utf8"), position))

    macro_wrapper = build_mac_wrapper(macros, macro_lookup)

    main_src = binutils.disassemble(main_sexp)
    macro_wrapper_src = binutils.disassemble(macro_wrapper)

    from .bindings import EVAL_F

    compiled_main_src = "(opt (com %s %s))" % (main_src, macro_wrapper_src)
    expanded_main = EVAL_F(EVAL_F, binutils.assemble(compiled_main_src), null)

    if not defuns:
        # no functions, just macros
        return expanded_main

    imps = []
    for _ in pre_subtituted_imps:
        sub_sexp = _.to([b"opt", [b"com", [QUOTE_KW, _], macro_wrapper]])
        imps.append(EVAL_F(EVAL_F, sub_sexp, null))
    imps_sexp = args.to(imps)

    imps_tree_prog = build_tree_prog(
        list([QUOTE_KW, _] for _ in imps_sexp.as_iter()))
    imps_tree = imps_sexp.to(imps_tree_prog)

    entry_src = "(e (q %s) (c %s (a))))" % (
        expanded_main, imps_tree)

    return binutils.assemble(entry_src)
