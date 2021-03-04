ATOM_MATCH = b"$"
SEXP_MATCH = b":"


def unify_bindings(bindings, new_key, new_value):
    """
    Try to add a new binding to the list, rejecting it if it conflicts
    with an existing binding.
    """
    new_key = bytes(new_key).decode()
    if new_key in bindings:
        if bindings[new_key] != new_value:
            return None
        return bindings
    new_bindings = dict(bindings)
    new_bindings[new_key] = new_value
    return new_bindings


def match(pattern, sexp, known_bindings={}):
    """
    Determine if sexp matches the pattern, with the given known bindings already applied.

    Returns None if no match, or a (possibly empty) dictionary of bindings if there is a match

    Patterns look like this:

    ($ . $) matches the literal "$", no bindings (mostly useless)
    (: . :) matches the literal ":", no bindings (mostly useless)

    ($ . A) matches B iff B is an atom; and A is bound to B
    (: . A) matches B always; and A is bound to B

    (A . B) matches (C . D) iff A matches C and B matches D
          and bindings are the unification (as long as unification is possible)
    """

    if not pattern.listp():
        if sexp.listp():
            return None
        return known_bindings if pattern.as_atom() == sexp.as_atom() else None

    left = pattern.first()
    right = pattern.rest()
    atom = sexp.as_atom()

    if left == ATOM_MATCH:
        if sexp.listp():
            return None
        if right == ATOM_MATCH:
            if atom == ATOM_MATCH:
                return {}
            return None
        return unify_bindings(known_bindings, right.as_atom(), sexp)

    if left == SEXP_MATCH:
        if right == SEXP_MATCH:
            if atom == SEXP_MATCH:
                return {}
            return None
        return unify_bindings(known_bindings, right.as_atom(), sexp)

    if not sexp.listp():
        return None

    new_bindings = match(left, sexp.first(), known_bindings)
    if new_bindings is None:
        return new_bindings
    return match(right, sexp.rest(), new_bindings)
