from clvm import KEYWORD_TO_ATOM

from clvm_tools.pattern_match import match
from clvm_tools.binutils import assemble

from clvm_tools.NodePath import NodePath, LEFT, RIGHT
from .helpers import quote

QUOTE_ATOM = KEYWORD_TO_ATOM["q"]
APPLY_ATOM = KEYWORD_TO_ATOM["a"]
FIRST_ATOM = KEYWORD_TO_ATOM["f"]
REST_ATOM = KEYWORD_TO_ATOM["r"]
CONS_ATOM = KEYWORD_TO_ATOM["c"]
RAISE_ATOM = KEYWORD_TO_ATOM["x"]

DEBUG_OPTIMIZATIONS = 0


def non_nil(sexp):
    return sexp.listp() or len(sexp.as_atom()) > 0


def seems_constant(sexp):
    if not sexp.listp():
        # note that `0` is a constant
        return not non_nil(sexp)
    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_ATOM:
            return True
        if as_atom == RAISE_ATOM:
            return False
    elif not seems_constant(operator):
        return False
    return all(seems_constant(_) for _ in sexp.rest().as_iter())


def constant_optimizer(r, eval):
    """
    If the expression does not depend upon @ anywhere,
    it's a constant. So we can simply evaluate it and
    return the quoted result.
    """
    if seems_constant(r) and non_nil(r):
        cost, r1 = eval(r, r.null())
        r = r.to(quote(r1))
    return r


def is_args_call(r):
    if not r.listp() and r.as_int() == 1:
        return True
    return False


CONS_Q_A_OPTIMIZER_PATTERN = assemble("(a (q . (: . sexp)) (: . args))")


def cons_q_a_optimizer(r, eval):
    """
    This applies the transform
    (a (q . SEXP) @) => SEXP
    """
    t1 = match(CONS_Q_A_OPTIMIZER_PATTERN, r)
    if t1 and is_args_call(t1["args"]):
        return t1["sexp"]
    return r


CONS_PATTERN = assemble("(c (: . first) (: . rest)))")


def cons_f(args):
    t = match(CONS_PATTERN, args)
    if t:
        return t["first"]
    return args.to([FIRST_ATOM, args])


def cons_r(args):
    t = match(CONS_PATTERN, args)
    if t:
        return t["rest"]
    return args.to([REST_ATOM, args])


def path_from_args(sexp, new_args):
    v = sexp.as_int()
    if v <= 1:
        return new_args
    sexp = sexp.to(v >> 1)
    if v & 1:
        return path_from_args(sexp, cons_r(new_args))
    return path_from_args(sexp, cons_f(new_args))


def sub_args(sexp, new_args):
    if sexp.nullp() or not sexp.listp():
        return path_from_args(sexp, new_args)

    first = sexp.first()
    if first.listp():
        first = sub_args(first, new_args)
    else:
        op = first.as_atom()

        if op == QUOTE_ATOM:
            return sexp

    return sexp.to([first] + [sub_args(_, new_args) for _ in sexp.rest().as_iter()])


VAR_CHANGE_OPTIMIZER_CONS_EVAL_PATTERN = assemble("(a (q . (: . sexp)) (: . args))")


def var_change_optimizer_cons_eval(r, eval):
    """
    This applies the transform
    (a (q . (op SEXP1...)) (ARGS)) => (q . RET_VAL) where ARGS != @
    via
    (op (a SEXP1 (ARGS)) ...) (ARGS)) and then "children_optimizer" of this.
    In some cases, this can result in a constant in some of the children.

    If we end up needing to push the "change of variables" to only one child, keep
    the optimization. Otherwise discard it.
    """

    t1 = match(VAR_CHANGE_OPTIMIZER_CONS_EVAL_PATTERN, r)

    if t1 is None:
        return r

    original_args = t1["args"]

    original_call = t1["sexp"]

    new_eval_sexp_args = sub_args(original_call, original_args)

    # Do not iterate into a quoted value as if it were a list
    if seems_constant(new_eval_sexp_args):
        new_operands = new_eval_sexp_args
        opt_operands = optimize_sexp(new_operands, eval)
        return r.to(opt_operands)

    new_operands = list(new_eval_sexp_args.as_iter())
    opt_operands = [optimize_sexp(_, eval) for _ in new_operands]
    non_constant_count = sum(1 if _.listp() and _.first() != QUOTE_ATOM else 0 for _ in opt_operands)
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
        if op == QUOTE_ATOM:
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


FIRST_ATOM_PATTERN = assemble("(f ($ . atom))")
REST_ATOM_PATTERN = assemble("(r ($ . atom))")


def path_optimizer(r, eval):
    """
    This applies the transform
    (f N) => A
    and
    (r N) => B
    """

    t1 = match(FIRST_ATOM_PATTERN, r)
    if t1 and non_nil(t1["atom"]):
        node = NodePath(t1["atom"].as_int())
        node = node + LEFT
        return r.to(node.as_short_path())

    t1 = match(REST_ATOM_PATTERN, r)
    if t1 and non_nil(t1["atom"]):
        node = NodePath(t1["atom"].as_int())
        node = node + RIGHT
        return r.to(node.as_short_path())
    return r


QUOTE_PATTERN_1 = assemble("(q . 0)")


def quote_null_optimizer(r, eval):
    """
    This applies the transform `(q . 0)` => `0`
    """
    t1 = match(QUOTE_PATTERN_1, r)
    if t1 is not None:
        return r.to(0)

    return r


APPLY_NULL_PATTERN_1 = assemble("(a 0 . (: . rest))")


def apply_null_optimizer(r, eval):
    """
    This applies the transform `(a 0 ARGS)` => `0`
    """
    t1 = match(APPLY_NULL_PATTERN_1, r)
    if t1 is not None:
        return r.to(0)

    return r


def optimize_sexp(r, eval):
    """
    Optimize an s-expression R written for clvm to R_opt where
    (a R args) == (a R_opt args) for ANY args.
    """
    if r.nullp() or not r.listp():
        return r

    OPTIMIZERS = [
        cons_optimizer,
        constant_optimizer,
        cons_q_a_optimizer,
        var_change_optimizer_cons_eval,
        children_optimizer,
        path_optimizer,
        quote_null_optimizer,
        apply_null_optimizer,
    ]

    while r.listp():
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
    return r


def make_do_opt(run_program):

    def do_opt(args):
        return 1, optimize_sexp(args.first(), run_program)

    return do_opt
