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
]


DEFAULT_MACRO_LOOKUP = None


def build_default_macro_lookup(eval_f):
    run = binutils.assemble("(opt (com (f (a)) (r (a))))")
    macro_lookup = to_sexp_f([])
    for macro_src in DEFAULT_MACROS_SRC:
        macro_sexp = binutils.assemble(macro_src)
        new_macro = eval_f(eval_f, run, macro_sexp.to((macro_sexp, macro_lookup)))
        macro_lookup = new_macro.rest().first().cons(macro_lookup)
    return macro_lookup


def default_macro_lookup(eval_f):
    global DEFAULT_MACRO_LOOKUP
    if DEFAULT_MACRO_LOOKUP is None:
        DEFAULT_MACRO_LOOKUP = to_sexp_f([])
        DEFAULT_MACRO_LOOKUP = build_default_macro_lookup(eval_f)
    return DEFAULT_MACRO_LOOKUP
