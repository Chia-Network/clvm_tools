from clvm import KEYWORD_TO_ATOM

from clvm_tools.pattern_match import match
from clvm_tools.binutils import assemble


QUOTE_KW = KEYWORD_TO_ATOM["q"]
ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]
RAISE_KW = KEYWORD_TO_ATOM["x"]

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
        if as_atom == RAISE_KW:
            return False
    elif not seems_constant(operator):
        return False
    return all(seems_constant(_) for _ in sexp.rest().as_iter())


def constant_optimizer(r, eval):
    """
    If the expression does not depend upon (a) anywhere,
    it's a constant. So we can simply evaluate it and
    return the quoted result.
    """
    if seems_constant(r):
        cost, r1 = eval(r, r.null())
        r = r.to([QUOTE_KW, r1])
    return r


def is_args_call(r):
    p = r.as_python()
    if p == [ARGS_KW]:
        return True
    if not r.listp() and r.as_int() in (0, 1):
        return True
    return False


CONS_Q_A_OPTIMIZER_PATTERN = assemble("((c (q (: . sexp)) (: . args)))")


def cons_q_a_optimizer(r, eval):
    """
    This applies the transform
    ((c (q SEXP) (a))) => SEXP
    """
    t1 = match(CONS_Q_A_OPTIMIZER_PATTERN, r)
    if t1 and is_args_call(t1["args"]):
        return t1["sexp"]
    return r


def sub_args(sexp, new_args):
    if sexp.nullp() or not sexp.listp():
        return sexp

    first = sexp.first()
    if not first.listp():
        op = first.as_atom()
        if op == ARGS_KW:
            return new_args

        if op == QUOTE_KW:
            return sexp

    return sexp.to([sub_args(_, new_args) for _ in sexp.as_iter()])


VAR_CHANGE_OPTIMIZER_CONS_EVAL_PATTERN = assemble("((c (q (: . sexp)) (: . args)))")


def var_change_optimizer_cons_eval(r, eval):
    """
    This applies the transform
    ((c (q (op SEXP1...)) (ARGS))) => (q RET_VAL) where ARGS != (a)
    via
    (op ((c SEXP1 (ARGS)) ...)) (ARGS)) and then "children_optimizer" of this.
    In some cases, this can result in a constant in some of the children.

    If we end up needing to push the "change of variables" to only one child, keep
    the optimization. Otherwise discard it.
    """

    t1 = match(VAR_CHANGE_OPTIMIZER_CONS_EVAL_PATTERN, r)

    if t1 is None:
        return r

    original_args = t1["args"]

    if is_args_call(original_args):
        return r

    original_call = t1["sexp"]

    new_eval_sexp_args = sub_args(original_call, original_args)

    new_operands = list(new_eval_sexp_args.as_iter())
    opt_operands = [optimize_sexp(_, eval) for _ in new_operands]
    non_constant_count = sum(1 if _.listp() and _.first() != QUOTE_KW else 0 for _ in opt_operands)
    if non_constant_count < 1:
        final_sexp = r.to(opt_operands)
        return final_sexp
    return r


def children_optimizer(r, eval):
    """
    Recursively apply optimizations to all non-quoted child nodes.
    """
    if not r.listp():
        return r
    operator = r.first()
    if not operator.listp():
        op = operator.as_atom()
        if op == QUOTE_KW:
            return r
    return r.to([optimize_sexp(_, eval) for _ in r.as_iter()])


CONS_OPTIMIZER_PATTERN_FIRST = assemble("(f (c (: . first) (: . rest)))")
CONS_OPTIMIZER_PATTERN_REST = assemble("(r (c (: . first) (: . rest)))")


def cons_optimizer(r, eval):
    """
    This applies the transform
    (f (c A B)) => A
    and
    (r (c A B)) => B
    """
    t1 = match(CONS_OPTIMIZER_PATTERN_FIRST, r)
    if t1:
        return t1["first"]
    t1 = match(CONS_OPTIMIZER_PATTERN_REST, r)
    if t1:
        return t1["rest"]
    return r


def optimize_sexp(r, eval):
    """
    Optimize an s-expression R written for clvm to R_opt where
    (e R args) == (e R_opt args) for ANY args.
    """
    if r.nullp() or not r.listp():
        return r

    OPTIMIZERS = [
        cons_optimizer,
        constant_optimizer,
        cons_q_a_optimizer,
        var_change_optimizer_cons_eval,
        children_optimizer,
    ]

    while True:
        start_r = r
        for opt in OPTIMIZERS:
            r = opt(r, eval)
            if start_r != r:
                break
        if start_r == r:
            return r
        if DEBUG_OPTIMIZATIONS:
            print("OPT-%s[%s] => %s\n" % (
                opt.__name__, start_r, r))


def do_opt(args):
    from .bindings import run_program
    return 1, optimize_sexp(args.first(), run_program)
