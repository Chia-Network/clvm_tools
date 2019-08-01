from clvm import casts
from clvm import eval_f, to_sexp_f

from .compile import op_compile_op, do_compile_list, do_compile_if


def do_test(args, eval_f):
    return to_sexp_f(args.first())


EXTRA_KEYWORDS = {
    30: do_test,
    32: op_compile_op,
    33: do_compile_list,
    34: do_compile_if,
}


def make_patched_eval_f(old_eval_f, keyword_operator_dict):
    def new_eval_f(eval_f, sexp, env):
        if sexp.listp() and not sexp.nullp():
            operator = casts.int_from_bytes(sexp.first().as_atom())
            f = keyword_operator_dict.get(operator)
            if f:
                args_list = [
                    eval_f(eval_f, _, env) for _ in sexp.rest().as_iter()]
                args = to_sexp_f(args_list)
                return f(args, eval_f)

        return old_eval_f(eval_f, sexp, env)
    return new_eval_f


COMPILER_EVAL_F = make_patched_eval_f(eval_f, EXTRA_KEYWORDS)


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
