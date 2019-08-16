from clvm import eval_f

from opacity import binutils
from opacity.patch_eval_f import bind_eval_f

from .compile import do_com, do_exp
from .macros import default_macro_lookup
from .optimize import do_opt


def do_mac(sexp, eval_f):
    return default_macro_lookup()


BINDINGS = {
    "com": do_com,
    "opt": do_opt,
    "exp": do_exp,
    "mac": do_mac,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)

brun = binutils.assemble("(e (f (a)) (r (a)))")
run = binutils.assemble("(e (com (f (a)) (mac)) (r (a)))")
