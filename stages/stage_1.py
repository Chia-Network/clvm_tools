from typing import List

from clvm.EvalError import EvalError
from clvm.chia_dialect import chia_dialect_with_op_table
from clvm.dialect import Dialect

from clvm_tools import binutils


def make_invocation(code, run_program):
    def invoke(args, max_cost):
        return run_program(code, args)

    return invoke


def make_bindings(bindings_sexp, run_program):
    binding_table = {}
    for pair in bindings_sexp.as_iter():
        name = pair.first().as_atom()
        binding_table[name] = make_invocation(pair.rest().first(), run_program)
    return binding_table


brun = run = binutils.assemble("(a 2 3)")


def dialect_for_search_paths(search_paths: List[str], strict: bool) -> Dialect:
    dialect = chia_dialect_with_op_table(strict)

    extra_bindings = {}

    def do_bind(args, max_cost):
        if len(args.as_python()) != 3:
            raise EvalError("bind requires 3 arguments")
        bindings = args.first()
        sexp = args.rest().first()
        env = args.rest().rest().first()
        original_bindings = dict(extra_bindings)
        local_dialect = chia_dialect_with_op_table(strict)

        def local_run_program(program, args):
            return local_dialect.run_program(
                program, args, max_cost=max_cost, pre_eval_f=None, to_python=sexp.to
            )

        new_bindings = make_bindings(bindings, local_run_program)
        extra_bindings.update(new_bindings)
        local_dialect.update(extra_bindings)
        cost, r = local_dialect.run_program(sexp, env, max_cost=max_cost, pre_eval_f=None, to_python=sexp.to)

        extra_bindings.clear()
        extra_bindings.update(original_bindings)

        return cost, r

    extra_bindings[b"bind"] = do_bind
    dialect.update(extra_bindings)
    return dialect
