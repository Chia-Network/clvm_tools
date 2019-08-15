
from clvm import eval_f

from opacity.patch_eval_f import bind_eval_f

from .prog import do_prog_op


def do_list(args, eval_f):
    return args


BINDINGS = {
    "prog_op": do_prog_op,
    "list": do_list,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)


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
