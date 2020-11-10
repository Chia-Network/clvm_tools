# read strings into Token

import io
from typing import Iterator

from clvm import casts, SExp
from clvm.serialize import sexp_to_stream

from .Type import Type
from .utils import ir_nullp, ir_type, ir_listp, ir_first, ir_rest, ir_as_atom, ir_val


def iter_sexp_format(ir_sexp: SExp) -> Iterator[str]:
    yield "("
    is_first = True
    while not ir_nullp(ir_sexp):
        if not ir_listp(ir_sexp):
            yield " . "
            yield from iter_ir_format(ir_sexp)
            break
        if not is_first:
            yield " "
        for _ in iter_ir_format(ir_first(ir_sexp)):
            yield _
        ir_sexp = ir_rest(ir_sexp)
        is_first = False
    yield ")"


def iter_ir_format(ir_sexp: SExp) -> Iterator[str]:
    if ir_listp(ir_sexp):
        yield from iter_sexp_format(ir_sexp)
        return

    type = ir_type(ir_sexp)

    if type == Type.CODE:
        bio = io.BytesIO()
        sexp_to_stream(ir_val(ir_sexp), bio)
        code = bio.getvalue().hex()
        yield "CODE[%s]" % code
        return

    if type == Type.NULL:
        yield "()"
        return

    atom = ir_as_atom(ir_sexp)

    if type == Type.INT:
        yield "%d" % casts.int_from_bytes(atom)
    elif type == Type.NODE:
        yield "NODE[%d]" % casts.int_from_bytes(atom)
    elif type == Type.HEX:
        yield "0x%s" % atom.hex()
    elif type == Type.QUOTES:
        yield '"%s"' % atom.decode("utf8")
    elif type == Type.DOUBLE_QUOTE:
        yield '"%s"' % atom.decode("utf8")
    elif type == Type.SINGLE_QUOTE:
        yield "'%s'" % atom.decode("utf8")
    elif type in (Type.SYMBOL, Type.OPERATOR):
        try:
            yield atom.decode("utf8")
        except UnicodeDecodeError:
            yield "(indecipherable symbol: %s)" % atom.hex()
    else:
        raise SyntaxError("bad ir format: %s" % ir_sexp)


def write_ir_to_stream(ir_sexp: SExp, f):
    for _ in iter_ir_format(ir_sexp):
        f.write(_)


def write_ir(ir_sexp: SExp) -> str:
    s = io.StringIO()
    write_ir_to_stream(ir_sexp, s)
    return s.getvalue()
