# read strings into Token

import io

from clvm import casts

from .Type import Type


def iter_sexp_format(sexp):
    yield "("
    is_first = True
    while not sexp.nullp():
        if not is_first:
            yield " "
        ir_sexp = sexp.first()
        for _ in iter_ir_format(ir_sexp):
            yield _
        ir_sexp = sexp.rest()
        type = casts.int_from_bytes(ir_sexp.first().as_atom())
        if type != Type.CONS:
            yield " . "
            yield from iter_ir_format(ir_sexp)
            break
        sexp = ir_sexp.rest()
        is_first = False
    yield ")"


def iter_ir_format(ir_sexp):
    type = casts.int_from_bytes(ir_sexp.first().as_atom())
    sexp = ir_sexp.rest()

    if type == Type.CONS:
        yield from iter_sexp_format(sexp)
        return

    atom = sexp.as_atom()
    if type == Type.INT:
        yield "%d" % casts.int_from_bytes(atom)
    elif type == Type.HEX:
        yield "0x%s" % atom.hex()
    elif type == Type.QUOTES:
        yield '"%s"' % atom.decode("utf8")
    elif type == Type.SYMBOL:
        try:
            yield atom.decode("utf8")
        except UnicodeDecodeError:
            yield "(undecypherable symbol: %s)" % atom.hex()
    else:
        raise SyntaxError("bad ir format: %s" % ir_sexp)


def write_ir_to_stream(ir_sexp, f):
    for _ in iter_ir_format(ir_sexp):
        f.write(_)


def write_ir(ir_sexp):
    s = io.StringIO()
    write_ir_to_stream(ir_sexp, s)
    return s.getvalue()
