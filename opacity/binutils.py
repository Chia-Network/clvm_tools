from clvm import casts
from clvm.runtime_001 import KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, to_sexp_f

from ir.reader import read_ir
from ir.writer import write_ir
from ir.Type import Type


def assemble_from_ir(ir_sexp):
    type = casts.int_from_bytes(ir_sexp.first().as_atom())
    sexp = ir_sexp.rest()

    if type in (Type.INT, Type.HEX, Type.QUOTES):
        return sexp

    if type == Type.SYMBOL:
        keyword = sexp.as_atom().decode("utf8")
        if keyword[:1] == "#":
            keyword = keyword[1:]
        atom = KEYWORD_TO_ATOM.get(keyword)
        if atom:
            return to_sexp_f(atom)
        raise SyntaxError("can't parse %s at %s" % (keyword, ir_sexp._offset))

    assert type == Type.CONS

    if sexp.nullp():
        return sexp

    # handle "quote" separately
    first_ir_sexp = sexp.first()
    if first_ir_sexp.first() == Type.SYMBOL and first_ir_sexp.rest() == b"quote":
        return to_sexp_f([KEYWORD_TO_ATOM["q"], sexp.rest()])

    sexp_1 = to_sexp_f(assemble_from_ir(sexp.first()))
    sexp_2 = assemble_from_ir(sexp.rest())
    return sexp_1.cons(sexp_2)


def disassemble_to_ir(sexp, allow_keyword=None):
    if sexp.nullp():
        return to_sexp_f((Type.CONS, []))

    if sexp.listp():
        if sexp.first().listp() or allow_keyword is None:
            allow_keyword = True
        v0 = disassemble_to_ir(sexp.first(), allow_keyword=allow_keyword)
        v1 = disassemble_to_ir(sexp.rest(), allow_keyword=False)
        return to_sexp_f((Type.CONS, (v0, v1)))

    as_atom = sexp.as_atom()
    if allow_keyword:
        v = KEYWORD_FROM_ATOM.get(as_atom)
        if v is not None and v != '.':
            return to_sexp_f((Type.SYMBOL, v.encode("utf8")))

    type = Type.INT
    if len(as_atom) > 4:
        type = Type.HEX
    return to_sexp_f((type, as_atom))


def disassemble(sexp):
    symbols = disassemble_to_ir(sexp)
    return write_ir(symbols)


def assemble(s):
    symbols = read_ir(s)
    return assemble_from_ir(symbols)
