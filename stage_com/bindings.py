from clvm import eval_f

from opacity import binutils
from opacity.patch_eval_f import bind_eval_f

from .compile import do_com
from .optimize import do_opt


BINDINGS = {
    "com": do_com,
    "opt": do_opt,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)

brun = binutils.assemble("(e (f (a)) (r (a)))")
run = binutils.assemble("(e (com (f (a))) (r (a)))")
