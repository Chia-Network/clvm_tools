from clvm_tools.binutils import assemble
from clvm_tools.pattern_match import match
from clvm.SExp import SExp

def test_pattern_match():

    r = match(assemble("$"), assemble("$"))
    assert r == {}

    r = match(assemble("($ . size)"), assemble("200"))
    assert r == {"size": assemble("200")}

    r = match(assemble("(: . size)"), assemble("200"))
    assert r == {"size": assemble("200")}

    r = match(assemble("($ . size)"), assemble("(I like cheese)"))
    assert r is None

    r = match(assemble("(: . size)"), assemble("(I like cheese)"))
    assert r == {"size": assemble("(I like cheese)")}

    r = match(assemble("(= (f (r (a))) ($ . pubkey))"), assemble("(= (f (r (a))) 50000)"))
    assert r == {"pubkey": assemble("50000")}

    r = match(assemble("(= (f (r (a))) ($ . pubkey1) ($ . pubkey2))"),
              assemble("(= (f (r (a))) 50000 60000)"))
    assert r == {"pubkey1": assemble("50000"), "pubkey2": assemble("60000")}

    r = match(assemble("(= (f (r (a))) ($ . pubkey1) ($ . pubkey1))"),
              assemble("(= (f (r (a))) 50000 60000)"))
    assert r is None

    r = match(assemble("(= (f (r (a))) ($ . pubkey1) ($ . pubkey1))"),
              assemble("(= (f (r (a))) 50000 50000)"))
    assert r == {"pubkey1": assemble("50000")}

    UNCURRY_PATTERN_FUNCTION = assemble("((c (q (: . function)) (: . core)))")
    p = assemble('((c (q (+ 2 5)) (c (q 200) (c (q 30) 1))))')
    r = match(UNCURRY_PATTERN_FUNCTION, p)
    assert r == {"function": assemble("(+ 2 5)"), "core": assemble("(c (q 200) (c (q 30) 1))")}
