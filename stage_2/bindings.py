from clvm import eval_cost

from clvm_tools import binutils
from clvm_tools.patch_eval_f import bind_eval_cost

from .compile import do_com
from .optimize import do_opt


BINDINGS = {
    "com": do_com,
    "opt": do_opt,
}


EVAL_COST = bind_eval_cost(eval_cost, BINDINGS)

brun = binutils.assemble("((c (f (a)) (r (a))))")
run = binutils.assemble("((c (opt (com (f (a)))) (r (a))))")
