from clvm import run_program, SExp, KEYWORD_TO_ATOM
from clvm.operators import OPERATOR_LOOKUP

from clvm_tools.binutils import assemble

from .pattern_match import match


# CURRY_OBJ_CODE contains compiled code from the output of the following:
# run -i clvm_runtime '(mod (F . args) (include curry.clvm) (curry_args F args))'

CURRY_OBJ_CODE = assemble(
    """
    ((c (q ((c 4 (c 2 (c 5 (c 7 (q ()))))))) (c (q ((c (c (q 5) (c (c (q 1) (c 5 (q ())))
    (c ((c 6 (c 2 (c 11 (q (q)))))) (q ())))) (q ())) (c (i 5 (q (c (q 5) (c (c (q 1)
    (c 9 (q ()))) (c ((c 6 (c 2 (c 13 (c 11 (q ())))))) (q ()))))) (q 11)) 1))) 1)))
"""
)


def curry(program, args):
    """
    ;; A "curry" binds values to a function, making them constant,
    ;; and returning a new function that returns fewer arguments (since the
    ;; arguments are now fixed).
    ;; Example: (defun add2 (V1 V2) (+ V1 V2))  ; add two values
    ;; (curry add2 15) ; this yields a function that accepts ONE argument, and adds 15 to it

    `program`: an SExp
    `args`: an SExp that is a list of constants to be bound to `program`
    """

    args = SExp.to((program, args))
    r = run_program(
        CURRY_OBJ_CODE,
        args,
        quote_kw=KEYWORD_TO_ATOM["q"],
        args_kw=KEYWORD_TO_ATOM["a"],
        operator_lookup=OPERATOR_LOOKUP,
    )
    return r


UNCURRY_PATTERN_FUNCTION = assemble("((c (q (: . function)) (: . core)))")
UNCURRY_PATTERN_CORE = assemble("(c (q (: . parm)) (: . core))")


def uncurry(curried_program):
    r = match(UNCURRY_PATTERN_FUNCTION, curried_program)
    if r is None:
        return r

    f = r["function"]
    core = r["core"]

    args = []
    while True:
        r = match(UNCURRY_PATTERN_CORE, core)
        if r is None:
            break
        args.append(r["parm"])
        core = r["core"]

    if core.as_python() == b"\x01":
        return f, f.to(args)
    return None
