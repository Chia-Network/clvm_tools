from stages.stage_0 import run_program as run_program_0
from stages.stage_0 import OPERATOR_LOOKUP

from clvm_tools import binutils

from .compile import do_com
from .optimize import do_opt


BINDINGS = {
    "com": do_com,
    "opt": do_opt,
}


brun = binutils.assemble("((c (f (a)) (r (a))))")
run = binutils.assemble("((c (opt (com (f (a)))) (r (a))))")


def run_program(
    program, args, max_cost=None, pre_eval_f=None,
):
    operator_lookup = dict(OPERATOR_LOOKUP)
    operator_lookup.update((k.encode("utf8"), v) for (k, v) in BINDINGS.items())
    return run_program_0(
        program,
        args,
        operator_lookup=operator_lookup,
        max_cost=max_cost,
        pre_eval_f=pre_eval_f,
    )
