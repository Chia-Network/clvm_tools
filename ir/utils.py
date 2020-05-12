from clvm import casts

from .Type import Type, CONS_TYPES


class pair(tuple):
    def __new__(cls, a, b):
        return tuple.__new__(cls, (a, b))

    def first(self):
        return self[0]

    def rest(self):
        return self[1]


def ir_new(type, val):
    return pair(type, val)


def ir_cons(first, rest):
    return pair(Type.CONS, pair(first, rest))


def ir_list(*items):
    if items:
        return ir_cons(items[0], ir_list(*items[1:]))
    return ir_null()


def ir_to(sexp, atom_type_f=lambda _: Type.SYMBOL):
    if sexp.nullp():
        return ir_null()
    if sexp.listp():
        return ir_cons(
            ir_to(sexp.first(), atom_type_f=atom_type_f),
            ir_to(sexp.rest(), atom_type_f=atom_type_f),
        )
    return ir_new(atom_type_f(sexp), sexp)


def ir_null():
    return pair(Type.NULL, [])


def ir_type(ir_sexp):
    the_type = ir_sexp.first()
    if the_type.listp():
        the_type = the_type.first()

    return casts.int_from_bytes(the_type.as_atom())


def ir_as_int(ir_sexp):
    return casts.int_from_bytes(ir_as_atom(ir_sexp))


def ir_offset(ir_sexp):
    the_offset = ir_sexp.first()
    if the_offset.listp():
        the_offset = the_offset.rest().as_atom()
    else:
        the_offset = b"\xff"
    return casts.int_from_bytes(the_offset)


def ir_val(ir_sexp):
    return ir_sexp.rest()


def ir_nullp(ir_sexp):
    return ir_type(ir_sexp) == Type.NULL


def ir_listp(ir_sexp):
    return ir_type(ir_sexp) in CONS_TYPES


def ir_as_sexp(ir_sexp):
    if ir_nullp(ir_sexp):
        return []
    if ir_type(ir_sexp) == Type.CONS:
        return ir_as_sexp(ir_first(ir_sexp)).cons(ir_as_sexp(ir_rest(ir_sexp)))
    return ir_sexp.rest()


def ir_is_atom(ir_sexp):
    return not ir_listp(ir_sexp)


def ir_as_atom(ir_sexp):
    return ir_sexp.rest().as_atom()


def ir_first(ir_sexp):
    return ir_sexp.rest().first()


def ir_rest(ir_sexp):
    return ir_sexp.rest().rest()


def ir_symbol(symbol):
    return (Type.SYMBOL, symbol.encode("utf8"))


def ir_as_symbol(ir_sexp):
    if ir_sexp.listp() and ir_type(ir_sexp) == Type.SYMBOL:
        return ir_as_sexp(ir_sexp).as_atom().decode("utf8")


def ir_iter(ir_sexp):
    while ir_listp(ir_sexp):
        yield ir_first(ir_sexp)
        ir_sexp = ir_rest(ir_sexp)


def is_ir(sexp):
    if sexp.nullp() or not sexp.listp():
        return False

    if sexp.first().listp():
        return False

    f = sexp.first().as_atom()
    if len(f) > 1:
        return False

    the_type = casts.int_from_bytes(f)
    try:
        t = Type(the_type)
    except ValueError:
        return False

    r = sexp.rest()
    if t == Type.CONS:
        if r.nullp():
            return True
        if r.listp():
            return is_ir(r.first()) and is_ir(r.rest())
        return False

    return not r.listp()
