from clvm import run_program as default_run_program  # noqa

try:
    from clvm.runtime_001 import KEYWORD_TO_ATOM, OPERATOR_LOOKUP  # noqa
except ImportError:
    from clvm.operators import KEYWORD_TO_ATOM, OPERATOR_LOOKUP  # noqa

from clvm_tools import binutils

brun = run = binutils.assemble("((c (f 1) (r 1)))")


def run_program(
    program,
    args,
    quote_kw=KEYWORD_TO_ATOM["q"],
    args_kw=KEYWORD_TO_ATOM["a"],
    operator_lookup=OPERATOR_LOOKUP,
    max_cost=None,
    pre_eval_f=None,
):
    return default_run_program(
        program, args, quote_kw, args_kw, operator_lookup, max_cost, pre_eval_f=pre_eval_f
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
