from clvm import casts
from clvm import to_sexp_f

from .Type import Type


def ir_cons(first, rest):
    return first.to((Type.CONS, (first, rest)))


def ir_null():
    return to_sexp_f((Type.CONS, []))


def ir_type(ir_sexp):
    return Type(casts.int_from_bytes(ir_sexp.first().as_atom()))


def ir_val(ir_sexp):
    return ir_sexp.rest()


def ir_nullp(ir_sexp):
    return ir_type(ir_sexp) == Type.CONS and ir_sexp.rest().nullp()


def ir_listp(ir_sexp):
    return ir_type(ir_sexp) == Type.CONS


def ir_as_sexp(ir_sexp):
    if ir_nullp(ir_sexp):
        return to_sexp_f([])
    if ir_type(ir_sexp) == Type.CONS:
        return ir_as_sexp(ir_first(ir_sexp)).cons(ir_as_sexp(ir_rest(ir_sexp)))
    return ir_sexp.rest()


def ir_is_atom(ir_sexp):
    return ir_type(ir_sexp) != Type.CONS


def ir_first(ir_sexp):
    return ir_sexp.rest().first()


def ir_rest(ir_sexp):
    return ir_sexp.rest().rest()


def ir_symbol(symbol):
    return to_sexp_f((Type.SYMBOL, symbol.encode("utf8")))


def ir_as_symbol(ir_sexp):
    if ir_sexp.listp() and ir_type(ir_sexp) == Type.SYMBOL:
        return ir_as_sexp(ir_sexp).as_atom().decode("utf8")


def ir_iter(ir_sexp):
    while True:
        if ir_type(ir_sexp) != Type.CONS:
            break
        if ir_nullp(ir_sexp):
            break
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
