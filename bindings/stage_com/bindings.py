from clvm import eval_f

from ..patch_eval_f import bind_eval_f, wrap_eval_f

from .compile import do_compile_op, do_compile_sexp


BINDINGS = {
    "compile_op": do_compile_op,
}


def compile_eval_f(function_bindings):

    def compile_transformer(sexp, env, local_eval_f):
        new_sexp = do_compile_sexp(sexp)
        return new_sexp, env

    return wrap_eval_f(bind_eval_f(eval_f, function_bindings), compile_transformer)


EVAL_F = compile_eval_f(BINDINGS)
