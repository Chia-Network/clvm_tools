from clvm import eval_f

from opacity.patch_eval_f import bind_eval_f

from .compile import do_com
from .mod import do_substitute_functions


BINDINGS = {
    "com": do_com,
    "substitute_functions": do_substitute_functions,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)
