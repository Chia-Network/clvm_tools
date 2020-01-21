from clvm import eval_cost

from clvm_tools import binutils
from clvm_tools.patch_eval_f import bind_eval_cost


def make_invocation(code):

    def invoke(args, eval_cost):
        cost, r = eval_cost(eval_cost, code, args)
        return r

    return invoke


def make_bindings(bindings_sexp):
    binding_table = {}
    for pair in bindings_sexp.as_iter():
        name = pair.first().as_atom().decode("utf8")
        binding_table[name] = make_invocation(pair.rest().first())
    return binding_table


def do_bind(args, eval_cost):
    if len(args.as_python()) != 3:
        raise SyntaxError("bind requires 3 arguments")
    bindings = args.first()
    sexp = args.rest().first()
    env = args.rest().rest().first()
    new_bindings = make_bindings(bindings)
    new_eval_cost = bind_eval_cost(eval_cost, new_bindings)
    return new_eval_cost(new_eval_cost, sexp, env)


BINDINGS = {
    "bind": do_bind,
}


EVAL_COST = bind_eval_cost(eval_cost, BINDINGS)

brun = run = binutils.assemble("((c (f (a)) (r (a))))")
