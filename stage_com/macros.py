from clvm import to_sexp_f


from opacity import binutils


DEFAULT_MACROS_SRC = [
    """
    (defmacro if (A B C)
        (qq (e
            (i (unquote A)
               (function (unquote B))
               (function (unquote C)))
            (a))))""",
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


def build_default_macro_lookup(eval_f):
    run = binutils.assemble("(opt (com (f (a)) (r (a))))")
    global DEFAULT_MACRO_LOOKUP
    for macro_src in DEFAULT_MACROS_SRC:
        macro_sexp = binutils.assemble(macro_src)
        env = macro_sexp.to((macro_sexp, DEFAULT_MACRO_LOOKUP))
        new_macro = eval_f(eval_f, run, env)
        DEFAULT_MACRO_LOOKUP = new_macro.rest().first().cons(
            DEFAULT_MACRO_LOOKUP)
    return DEFAULT_MACRO_LOOKUP


def default_macro_lookup(eval_f):
    global DEFAULT_MACRO_LOOKUP
    if DEFAULT_MACRO_LOOKUP is None:
        DEFAULT_MACRO_LOOKUP = to_sexp_f([])
        DEFAULT_MACRO_LOOKUP = build_default_macro_lookup(eval_f)
    return DEFAULT_MACRO_LOOKUP
