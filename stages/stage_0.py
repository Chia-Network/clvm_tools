from clvm import run_program as default_run_program  # noqa
from clvm.operators import OPERATOR_LOOKUP, OperatorDict
from clvm.EvalError import EvalError

from clvm_tools import binutils

def run_program(
    program,
    args,
    operator_lookup=OPERATOR_LOOKUP,
    max_cost=None,
    pre_eval_f=None,
    strict=False,
):
    if strict:
        def fatal_error(op, arguments):
            raise EvalError("unimplemented operator", arguments.to(op))
        operator_lookup = OperatorDict(operator_lookup, unknown_op_handler=fatal_error)

    return default_run_program(
        program,
        args,
        operator_lookup,
        max_cost,
        pre_eval_f=pre_eval_f,
    )


"""
Copyright 2019 Chia Network Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
