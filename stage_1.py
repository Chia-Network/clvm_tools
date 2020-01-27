from stage_0 import run_program as run_program_0
from stage_0 import OPERATOR_LOOKUP
from clvm_tools import binutils


def make_invocation(code):
    def invoke(args, eval):
        cost, r = eval(code, args)
        return r

    invoke.needs_eval = 1

    return invoke


def make_bindings(bindings_sexp, eval):
    binding_table = {}
    for pair in bindings_sexp.as_iter():
        name = pair.first().as_atom()
        binding_table[name] = make_invocation(pair.rest().first())
    return binding_table


def do_bind(args, eval):
    if len(args.as_python()) != 3:
        raise SyntaxError("bind requires 3 arguments")
    bindings = args.first()
    sexp = args.rest().first()
    env = args.rest().rest().first()
    new_bindings = make_bindings(bindings, eval)
    original_operator_lookup = eval.operator_lookup
    eval.operator_lookup = dict(original_operator_lookup)
    eval.operator_lookup.update(new_bindings)
    cost, r = eval(sexp, env)
    eval.operator_lookup = original_operator_lookup
    return cost, r


do_bind.needs_eval = 1


BINDINGS = {
    "bind": do_bind,
}


brun = run = binutils.assemble("((c (f (a)) (r (a))))")


def run_program(
    program, args, max_cost=None, pre_eval_f=None, post_eval_f=None,
):
    operator_lookup = dict(OPERATOR_LOOKUP)
    operator_lookup.update((k.encode("utf8"), v) for (k, v) in BINDINGS.items())
    return run_program_0(
        program,
        args,
        operator_lookup=operator_lookup,
        max_cost=max_cost,
        pre_eval_f=pre_eval_f,
        post_eval_f=post_eval_f,
    )
