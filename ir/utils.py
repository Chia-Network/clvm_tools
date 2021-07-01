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


def ir_null() -> SExp:
    return ir_new(Type.NULL, 0)


def ir_type(ir_sexp: SExp) -> int:
    the_type = ir_sexp.first()
    if the_type.listp():
        the_type = the_type.first()

    return casts.int_from_bytes(the_type.as_atom())


def ir_as_int(ir_sexp: SExp) -> int:
    return casts.int_from_bytes(ir_as_atom(ir_sexp))


def ir_offset(ir_sexp: SExp) -> int:
    the_offset = ir_sexp.first()
    if the_offset.listp():
        the_offset = the_offset.rest().as_atom()
    else:
        the_offset = b"\xff"
    return casts.int_from_bytes(the_offset)


def ir_val(ir_sexp: SExp) -> SExp:
    return ir_sexp.rest()


def ir_nullp(ir_sexp: SExp) -> bool:
    return ir_type(ir_sexp) == Type.NULL


def ir_listp(ir_sexp: SExp) -> bool:
    return ir_type(ir_sexp) in CONS_TYPES


def ir_as_sexp(ir_sexp: SExp) -> SExp:
    if ir_nullp(ir_sexp):
        return []
    if ir_type(ir_sexp) == Type.CONS:
        return ir_as_sexp(ir_first(ir_sexp)).cons(ir_as_sexp(ir_rest(ir_sexp)))
    return ir_sexp.rest()


def ir_is_atom(ir_sexp: SExp) -> bool:
    return not ir_listp(ir_sexp)


def ir_as_atom(ir_sexp: SExp) -> bytes:
    return bytes(ir_sexp.rest().as_atom())


def ir_first(ir_sexp: SExp) -> SExp:
    return ir_sexp.rest().first()


def ir_rest(ir_sexp: SExp) -> SExp:
    return ir_sexp.rest().rest()


def ir_symbol(symbol) -> typing.Tuple[Type, str]:
    return (Type.SYMBOL, symbol.encode("utf8"))


def ir_as_symbol(ir_sexp: SExp) -> typing.Optional[str]:
    if ir_sexp.listp() and ir_type(ir_sexp) == Type.SYMBOL:
        return bytes(ir_as_sexp(ir_sexp).as_atom()).decode("utf8")
    return None


def ir_iter(ir_sexp: SExp) -> typing.Iterable[SExp]:
    while ir_listp(ir_sexp):
        yield ir_first(ir_sexp)
        ir_sexp = ir_rest(ir_sexp)


def is_ir(sexp) -> bool:
    if sexp.atom is not None:
        return False

    type_sexp, val_sexp = sexp.pair
    f = type_sexp.atom
    if f is None or len(f) > 1:
        return False

    the_type = casts.int_from_bytes(f)
    try:
        t = Type(the_type)
    except ValueError:
        return False

    if t == Type.CONS:
        if val_sexp.atom == b"":
            return True
        if val_sexp.pair:
            return all(is_ir(_) for _ in val_sexp.pair)
        return False

    return val_sexp.atom is not None
