from clvm import eval_f

from opacity.patch_eval_f import bind_eval_f

from .compile import do_com


BINDINGS = {
    "com": do_com,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)
