"""
Stage 1 was a first attempt at making it possible to write complex code that
calls functions by name by adding a opcode bind to the language that allows
additional opcodes to be added to the language dynamically, associating a
function name with clvm code. An example is the factorial function in
`tests/stage_1/fact-1.txt`

This has drawbacks: a second namespace for `bind` that takes on python-like
characteristics which can leak environment data. So stage 1 is a dead end. The
code is still being maintained, but just barely, and should eventually be
removed.
"""


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
