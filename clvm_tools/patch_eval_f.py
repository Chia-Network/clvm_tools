
from clvm.make_eval import DEFAULT_APPLY_COST


def bind_eval_cost(old_eval_cost, binding_table):
    def new_eval_cost(eval_cost, sexp, env, current_cost=0, max_cost=1000000):
        if sexp.listp() and not sexp.nullp() and not sexp.first().listp():
            operator = sexp.first().as_atom()
            try:
                symbol = operator.decode("utf8")
            except UnicodeDecodeError:
                symbol = None
            f = binding_table.get(symbol)
            if f:
                args_list = []
                for _ in sexp.rest().as_iter():
                    current_cost, r = eval_cost(eval_cost, _, env, current_cost, max_cost)
                    args_list.append(r)
                args = sexp.to(args_list)

                r = f(args, eval_cost)
                additional_cost = DEFAULT_APPLY_COST
                if isinstance(r, (tuple,)):
                    additional_cost, r = r
                return current_cost + additional_cost, r

        return old_eval_cost(eval_cost, sexp, env, current_cost, max_cost)
    return new_eval_cost


def bind_eval_f(old_eval_f, binding_table):
    def new_eval_f(eval_f, sexp, env):
        if sexp.listp() and not sexp.nullp() and not sexp.first().listp():
            operator = sexp.first().as_atom()
            try:
                symbol = operator.decode("utf8")
            except UnicodeDecodeError:
                symbol = None
            f = binding_table.get(symbol)
            if f:
                args_list = [
                    eval_f(eval_f, _, env) for _ in sexp.rest().as_iter()]
                args = sexp.to(args_list)
                return f(args, eval_f)

        return old_eval_f(eval_f, sexp, env)
    return new_eval_f


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
