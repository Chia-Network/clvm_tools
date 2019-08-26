from clvm import eval_f

from clvm_tools import binutils
from clvm_tools.patch_eval_f import bind_eval_f

from .compile import do_com, do_exp
from .defaults import default_macro_lookup
from .optimize import do_opt


BINDINGS = {
    "com": do_com,
    "opt": do_opt,
    "exp": do_exp,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)

brun = binutils.assemble("(e (f (a)) (r (a)))")
run = binutils.assemble("(e (opt (com (f (a)))) (r (a)))")
