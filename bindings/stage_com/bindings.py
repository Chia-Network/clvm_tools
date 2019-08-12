from clvm import eval_f, to_sexp_f

from ..patch_eval_f import bind_eval_f, wrap_eval_f

from .compile import do_compile_op, do_compile_sexp


DEFAULT_MACROS = [
    [b"if", [b"then"]]
]


BINDINGS = {
    "compile_op": do_compile_op,
}


def compile_eval_f(macro_lookup):

    macro_lookup = to_sexp_f(macro_lookup)

    def do_macro_lookup(sexp, eval_f):
        return macro_lookup

    bindings = dict(BINDINGS)
    bindings["macro_lookup"] = do_macro_lookup

    def compile_transformer(sexp, env, local_eval_f):
        new_sexp = do_compile_sexp(sexp, local_eval_f)
        return new_sexp, env

    return wrap_eval_f(bind_eval_f(eval_f, bindings), compile_transformer)


EVAL_F = compile_eval_f(DEFAULT_MACROS)
