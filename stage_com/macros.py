from clvm import to_sexp_f


from opacity import binutils


DEFAULT_MACROS_SRC = [
    "(defmacro if (A B C) (qq (e (i (unquote (com A (macros))) (q (unquote (com B (macros)))) (q (unquote (com C (macros))))) (a))))",
]


DEFAULT_MACRO_LOOKUP = None


def build_default_macro_lookup():
    #breakpoint()
    from .bindings import EVAL_F
    run = binutils.assemble("(com (f (a)) (r (a)))")
    macro_lookup = to_sexp_f([])
    for macro_src in DEFAULT_MACROS_SRC:
        macro_sexp = binutils.assemble(macro_src)
        new_macro = EVAL_F(EVAL_F, run, to_sexp_f((macro_sexp, macro_lookup)))
        macro_lookup = new_macro.rest().first().cons(macro_lookup)
    return macro_lookup


def default_macro_lookup():
    global DEFAULT_MACRO_LOOKUP
    if DEFAULT_MACRO_LOOKUP is None:
        DEFAULT_MACRO_LOOKUP = build_default_macro_lookup()
    return DEFAULT_MACRO_LOOKUP
