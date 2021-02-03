from stages.stage_0 import run_program as run_program_0
from stages.stage_0 import OPERATOR_LOOKUP
from clvm_tools import binutils
from clvm_tools.operator_dict import OperatorDict


def make_invocation(code):
    def invoke(args):
        return run_program(code, args)

    return invoke


def make_bindings(bindings_sexp):
    binding_table = {}
    for pair in bindings_sexp.as_iter():
        name = pair.first().as_atom()
        binding_table[name] = make_invocation(pair.rest().first())
    return binding_table


def do_bind(args):
    if len(args.as_python()) != 3:
        raise SyntaxError("bind requires 3 arguments")
    bindings = args.first()
    sexp = args.rest().first()
    env = args.rest().rest().first()
    new_bindings = make_bindings(bindings)
    original_operator_lookup = run_program.operator_lookup
    run_program.operator_lookup = OperatorDict(original_operator_lookup)
    run_program.operator_lookup.update(new_bindings)
    cost, r = run_program(sexp, env)
    run_program.operator_lookup = original_operator_lookup
    return cost, r


BINDINGS = {
    "bind": do_bind,
}


brun = run = binutils.assemble("((c (f 1) (r 1)))")


class RunProgram:
    def __init__(self):
        operator_lookup = OperatorDict(OPERATOR_LOOKUP)
        operator_lookup.update((k.encode("utf8"), v) for (k, v) in BINDINGS.items())
        self.operator_lookup = operator_lookup

    def __call__(self, program, args, max_cost=None, pre_eval_f=None, strict=False):
        return run_program_0(
            program,
            args,
            operator_lookup=self.operator_lookup,
            max_cost=max_cost,
            pre_eval_f=pre_eval_f,
            strict=strict,
        )


run_program = RunProgram()
