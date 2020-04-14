from stages.stage_0 import run_program as run_program_0

from clvm_tools import binutils

from .helpers import operators_for_context


brun = binutils.assemble("((a))")
run = binutils.assemble("((a))")


def run_program(
    program, args, max_cost=None, pre_eval_f=None,
):
    operator_lookup = operators_for_context([])
    return run_program_0(
        program,
        args,
        operator_lookup=operator_lookup,
        max_cost=max_cost,
        pre_eval_f=pre_eval_f,
    )
