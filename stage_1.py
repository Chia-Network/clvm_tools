from clvm import eval_f

from opacity.patch_eval_f import bind_eval_f


def make_invocation(code):

    def invoke(args, eval_f):
        r = eval_f(eval_f, code, args)
        return r

    return invoke


def make_bindings(bindings_sexp):
    binding_table = {}
    for pair in bindings_sexp.as_iter():
        name = pair.first().as_atom().decode("utf8")
        binding_table[name] = make_invocation(pair.rest().first())
    return binding_table


def do_bind(args, eval_f):
    if len(args.as_python()) != 3:
        raise SyntaxError("bind requires 3 arguments")
    bindings = args.first()
    sexp = args.rest().first()
    env = args.rest().rest().first()
    new_bindings = make_bindings(bindings)
    new_eval_f = bind_eval_f(eval_f, new_bindings)
    return new_eval_f(new_eval_f, sexp, env)


BINDINGS = {
    "bind": do_bind,
}


EVAL_F = bind_eval_f(eval_f, BINDINGS)
