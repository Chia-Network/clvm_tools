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
    the_type = ir_sexp.pair[0]
    if the_type.pair:
        the_type = the_type.pair[0]

    return casts.int_from_bytes(the_type.atom)


def ir_as_int(ir_sexp):
    return casts.int_from_bytes(ir_as_atom(ir_sexp))


def ir_offset(ir_sexp):
    the_offset = ir_sexp.pair[0]
    if the_offset.pair:
        the_offset = the_offset.pair[1].atom
    else:
        the_offset = b"\xff"
    return casts.int_from_bytes(the_offset)


def ir_val(ir_sexp):
    return ir_sexp.pair[1]


def ir_nullp(ir_sexp):
    return ir_type(ir_sexp) == Type.NULL


def ir_listp(ir_sexp):
    return ir_type(ir_sexp) in CONS_TYPES


def ir_as_sexp(ir_sexp):
    if ir_nullp(ir_sexp):
        return []
    if ir_type(ir_sexp) == Type.CONS:
        return ir_as_sexp(ir_first(ir_sexp)).cons(ir_as_sexp(ir_rest(ir_sexp)))
    return ir_sexp.pair[1]


def ir_is_atom(ir_sexp):
    return not ir_listp(ir_sexp)


def ir_as_atom(ir_sexp):
    return ir_sexp.pair[1].atom


def ir_first(ir_sexp):
    return ir_sexp.pair[1].pair[0]


def ir_rest(ir_sexp):
    return ir_sexp.pair[1].pair[1]


def ir_symbol(symbol):
    return (Type.SYMBOL, symbol.encode("utf8"))


def ir_as_symbol(ir_sexp):
    if ir_sexp.pair and ir_type(ir_sexp) == Type.SYMBOL:
        return ir_as_sexp(ir_sexp).atom.decode("utf8")


def ir_iter(ir_sexp):
    while ir_listp(ir_sexp):
        yield ir_first(ir_sexp)
        ir_sexp = ir_rest(ir_sexp)


def is_ir(sexp):
    if sexp.nullp() or not sexp.pair:
        return False

    if sexp.pair[0].pair:
        return False

    f = sexp.pair[0].atom
    if len(f) > 1:
        return False

    the_type = casts.int_from_bytes(f)
    try:
        t = Type(the_type)
    except ValueError:
        return False

    r = sexp.pair[1]
    if t == Type.CONS:
        if r.nullp():
            return True
        if r.pair:
            return is_ir(r.pair[0]) and is_ir(r.pair[1])
        return False

    return not r.pair
