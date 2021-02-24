from clvm.operators import KEYWORD_TO_ATOM

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
    PLUS = KEYWORD_TO_ATOM["+"][0]
    f = assemble("(+ 2 5)")
    args = assemble("(200 30)")
    actual_disassembly = check_idempotency(f, args)
    assert actual_disassembly == f"(a (q {PLUS} 2 5) (c (q . 200) (c (q . 30) 1)))"

    f = assemble("(+ 2 5)")
    args = assemble("((+ (q . 50) (q . 60)))")
    actual_disassembly = check_idempotency(f, args)
    assert actual_disassembly == f"(a (q {PLUS} 2 5) (c (q {PLUS} (q . 50) (q . 60)) 1))"
