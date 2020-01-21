from clvm import to_sexp_f


from clvm_tools import binutils


DEFAULT_MACROS_SRC = [
    """
    (defmacro if (A B C)
        (qq ((c
            (i (unquote A)
               (function (unquote B))
               (function (unquote C)))
            (a)))))""",
    """
    (defmacro and ARGS
        (if ARGS
            (qq (if (unquote (f ARGS))
                (unquote (c and (r ARGS)))
                ()
                ))
            1)
        )""",
]


DEFAULT_MACRO_LOOKUP = None


def build_default_macro_lookup(eval_cost):
    run = binutils.assemble("((c (com (f (a)) (r (a))) (a)))")
    global DEFAULT_MACRO_LOOKUP
    for macro_src in DEFAULT_MACROS_SRC:
        macro_sexp = binutils.assemble(macro_src)
        env = macro_sexp.to((macro_sexp, DEFAULT_MACRO_LOOKUP))
        cost, new_macro = eval_cost(eval_cost, run, env)
        DEFAULT_MACRO_LOOKUP = new_macro.cons(
            DEFAULT_MACRO_LOOKUP)
    return DEFAULT_MACRO_LOOKUP


def default_macro_lookup(eval_cost):
    global DEFAULT_MACRO_LOOKUP
    if DEFAULT_MACRO_LOOKUP is None:
        DEFAULT_MACRO_LOOKUP = to_sexp_f([])
        DEFAULT_MACRO_LOOKUP = build_default_macro_lookup(eval_cost)
    return DEFAULT_MACRO_LOOKUP
