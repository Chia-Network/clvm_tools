from clvm import KEYWORD_TO_ATOM


QUOTE_KW = KEYWORD_TO_ATOM["q"]
ARGS_KW = KEYWORD_TO_ATOM["a"]
EVAL_KW = KEYWORD_TO_ATOM["e"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]

DEBUG_OPTIMIZATIONS = 0


def seems_constant(sexp):
    if sexp.nullp() or not sexp.listp():
        return False
    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return True
        if as_atom == ARGS_KW:
            return False
    return all(seems_constant(_) for _ in sexp.rest().as_iter())


def constant_optimizer(r, eval_f):
    """
    If the expression does not depend upon (a) anywhere,
    it's a constant. So we can simply evaluate it and
    return the quoted result.
    """
    if seems_constant(r):
        r1 = eval_f(eval_f, r, r.null())
        r = r.to([QUOTE_KW, r1])
    return r


def eval_q_a_optimizer(r, eval_f):
    """
    This applies the transform
    (e (q SEXP) (a)) => SEXP
    """
    if r.nullp() or not r.listp():
        return r
    operator = r.first()
    if operator.listp():
        return r

    as_atom = operator.as_atom()
    if as_atom != EVAL_KW:
        return r
    first_arg = r.rest().first()
    if not first_arg.listp() or first_arg.nullp():
        return r
    op_2 = first_arg.first()
    if op_2.listp() or op_2.as_atom() != QUOTE_KW:
        return r
    if r.rest().rest().as_python() != [[ARGS_KW]]:
        return r
    return first_arg.rest().first()


def sub_args(sexp, new_args):
    if sexp.nullp() or not sexp.listp():
        return sexp

    op = sexp.first().as_atom()
    if op == ARGS_KW:
        return new_args

    if op == QUOTE_KW:
        return sexp

    return sexp.to([op] + [sub_args(_, new_args) for _ in sexp.rest().as_iter()])


def var_change_optimizer(r, eval_f):
    """
    This applies the transform
    (e (q (op SEXP1...)) (ARGS)) => (q RET_VAL) where ARGS != (a)
    via
    (op (e SEXP1 (ARGS)) ...)) (ARGS)) and then "children_optimizer" of this.
    In some cases, this can result in a constant in some of the children.

    If we end up needing to push the "change of variables" to only one child, keep
    the optimization. Otherwise discard it.
    """

    if r.nullp() or not r.listp():
        return r
    operator = r.first()
    if operator.listp():
        return r

    as_atom = operator.as_atom()
    if as_atom != EVAL_KW:
        return r
    first_arg = r.rest().first()
    if not first_arg.listp() or first_arg.nullp():
        return r
    op_2 = first_arg.first()
    if op_2.listp() or op_2.as_atom() != QUOTE_KW:
        return r
    new_args = r.rest().rest().first().as_python()
    if new_args == [ARGS_KW]:
        # let eval_q_a_optimizer take care of this
        return r

    inner_sexp = first_arg.rest().first()
    new_sexp = sub_args(inner_sexp, new_args)

    new_operands = list(new_sexp.rest().as_iter())
    opt_operands = [optimize_sexp(_, eval_f) for _ in new_operands]
    non_constant_count = sum(1 if _.first() != QUOTE_KW else 0 for _ in opt_operands)
    if non_constant_count < 1:
        final_sexp = r.to([first_arg.rest().first().first().as_atom()] + opt_operands)
        return final_sexp
    return r


def children_optimizer(r, eval_f):
    """
    Recursively apply optimizations to all non-quoted child nodes.
    """
    operator = r.first()
    if operator.listp():
        return r
    op = operator.as_atom()
    if op == QUOTE_KW:
        return r
    return r.to([op] + [optimize_sexp(_, eval_f) for _ in r.rest().as_iter()])


def cons_optimizer(r, eval_f):
    """
    This applies the transform
    (f (c A B)) => A
    and
    (r (c A B)) => B
    """
    if r.nullp() or not r.listp():
        return r
    operator = r.first()
    if operator.listp():
        return r

    as_atom = operator.as_atom()
    if as_atom not in (FIRST_KW, REST_KW):
        return r

    cons_sexp = r.rest().first()
    if cons_sexp.listp() and not cons_sexp.nullp():
        if cons_sexp.first().as_atom() == CONS_KW:
            if as_atom == FIRST_KW:
                return cons_sexp.rest().first()
            return cons_sexp.rest().rest().first()
    return r


def optimize_sexp(r, eval_f):
    """
    Optimize an s-expression R written for clvm to R_opt where
    (e R args) == (e R_opt args) for ANY args.
    """
    if r.nullp() or not r.listp():
        return r

    OPTIMIZERS = [
        cons_optimizer,
        constant_optimizer,
        eval_q_a_optimizer,
        var_change_optimizer,
        children_optimizer,
    ]

    while True:
        start_r = r
        for opt in OPTIMIZERS:
            r = opt(r, eval_f)
            if start_r != r:
                break
        if start_r == r:
            return r
        if DEBUG_OPTIMIZATIONS:
            print("OPT-%s[%s] => %s\n" % (
                opt.__name__, start_r, r))


def do_opt(args, eval_f):
    return optimize_sexp(args.first(), eval_f)
