from clvm_tools.binutils import assemble
from clvm_tools.pattern_match import match


def test_pattern_match():

    r = match(assemble("($ . $)"), assemble("$"))
    assert r == {}

    r = match(assemble("($ . $)"), assemble("x"))
    assert r is None

    r = match(assemble("(: . :)"), assemble(":"))
    assert r == {}

    r = match(assemble("(: . :)"), assemble("x"))
    assert r is None

    r = match(assemble("$"), assemble("$"))
    assert r == {}

    # () is an atom
    r = match(assemble("($ . n)"), assemble("()"))
    assert r == {"n": assemble("()")}

    r = match(assemble("($ . size)"), assemble("200"))
    assert r == {"size": assemble("200")}

    r = match(assemble("(: . size)"), assemble("200"))
    assert r == {"size": assemble("200")}

    r = match(assemble("($ . size)"), assemble("(I like cheese)"))
    assert r is None

    r = match(assemble("(: . size)"), assemble("(I like cheese)"))
    assert r == {"size": assemble("(I like cheese)")}

    r = match(
        assemble("(= (f (r (a))) ($ . pubkey))"), assemble("(= (f (r (a))) 50000)")
    )
    assert r == {"pubkey": assemble("50000")}

    r = match(
        assemble("(= (f (r (a))) ($ . pubkey1) ($ . pubkey2))"),
        assemble("(= (f (r (a))) 50000 60000)"),
    )
    assert r == {"pubkey1": assemble("50000"), "pubkey2": assemble("60000")}

    r = match(
        assemble("(= (f (r (a))) ($ . pubkey1) ($ . pubkey1))"),
        assemble("(= (f (r (a))) 50000 60000)"),
    )
    assert r is None

    r = match(
        assemble("(= (f (r (a))) ($ . pubkey1) ($ . pubkey1))"),
        assemble("(= (f (r (a))) 50000 50000)"),
    )
    assert r == {"pubkey1": assemble("50000")}
