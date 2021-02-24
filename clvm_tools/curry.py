from clvm_tools.binutils import assemble

from stages.stage_0 import run_program

from .pattern_match import match


# CURRY_OBJ_CODE contains compiled code from the output of the following:
# run -i clvm_runtime '(mod (F . args) (include curry.clvm) (curry_args F args))'

# the text below has been hand-optimized to replace `((c (q X) Y))` with `(a (q X) Y)`
# and `(q 0)` with `0`

CURRY_OBJ_CODE = assemble(
    """
(a (q #a 4 (c 2 (c 5 (c 7 0)))) (c (q (c (q . 2) (c (c (q . 1) 5) (c (a 6 (c 2 (c 11 (q 1)))) 0))) #a (i 5 (q 4 (q . 4) (c (c (q . 1) 9) (c (a 6 (c 2 (c 13 (c 11 0)))) 0))) (q . 11)) 1) 1))
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

    args = program.to((program, args))
    r = run_program(CURRY_OBJ_CODE, args)
    return r


UNCURRY_PATTERN_FUNCTION = assemble("(a (q . (: . function)) (: . core))")
UNCURRY_PATTERN_CORE = assemble("(c (q . (: . parm)) (: . core))")


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
