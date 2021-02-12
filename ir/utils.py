import typing

from clvm import casts, SExp

from .Type import Type, CONS_TYPES

CastableType = typing.Any


def ir_new(type: int, val: CastableType, offset: typing.Optional[int] = None) -> SExp:
    if offset is not None:
        type = SExp.to((type, offset))
    return SExp.to((type, val))


def ir_cons(first: SExp, rest: SExp, offset: typing.Optional[int] = None) -> SExp:
    return ir_new(Type.CONS, ir_new(first, rest), offset)


def ir_list(*items) -> SExp:
    if items:
        return ir_cons(items[0], ir_list(*items[1:]))
    return ir_null()


def ir_null():
    return ir_new(Type.NULL, 0)


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
    return bytes(ir_sexp.rest().as_atom())


def ir_first(ir_sexp):
    return ir_sexp.rest().first()


def ir_rest(ir_sexp):
    return ir_sexp.rest().rest()


def ir_symbol(symbol):
    return (Type.SYMBOL, symbol.encode("utf8"))


def ir_as_symbol(ir_sexp):
    if ir_sexp.listp() and ir_type(ir_sexp) == Type.SYMBOL:
        return bytes(ir_as_sexp(ir_sexp).as_atom()).decode("utf8")


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
