import io

from clvm.serialize import sexp_to_stream

from clvm_tools.binutils import assemble, disassemble
from clvm_tools.curry import curry, uncurry


def check_idempotency(f, args):
    cost, curried = curry(f, args)

    r = disassemble(curried)
    f_0, args_0 = uncurry(curried)

    assert disassemble(f_0) == disassemble(f)
    assert disassemble(args_0) == disassemble(args)
    return r


def test_curry_uncurry():
    f = assemble("(+ 2 5)")
    args = assemble("(200 30)")
    actual_disassembly = check_idempotency(f, args)
    assert actual_disassembly == "((c (quote (+ 2 5)) (c (quote 200) (c (quote 30) 1))))"

    f = assemble("(+ 2 5)")
    args = assemble("((+ (quote 50) (quote 60)))")
    actual_disassembly = check_idempotency(f, args)
    assert actual_disassembly == "((c (quote (+ 2 5)) (c (quote (+ (quote 50) (quote 60))) 1)))"
