from clvm import casts
from clvm.runtime_001 import KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, to_sexp_f

from ir.reader import read_tokens
from ir.writer import write_tokens
from ir.Type import Type


def assemble_from_symbols(ir_sexp):
    type = casts.int_from_bytes(ir_sexp.first().as_atom())
    sexp = ir_sexp.rest()

    if type in (Type.INT, Type.HEX, Type.QUOTES):
        return sexp

    if type == Type.SYMBOL:
        keyword = sexp.as_atom().decode("utf8")
        atom = KEYWORD_TO_ATOM.get(keyword)
        if atom:
            return to_sexp_f(atom)
        raise SyntaxError("unknown keyword %s" % keyword)

    assert type == Type.CONS

    if sexp.nullp():
        return sexp

    sexp_1 = to_sexp_f(assemble_from_symbols(sexp.first()))
    sexp_2 = assemble_from_symbols(sexp.rest())
    return sexp_1.cons(sexp_2)


def disassemble_to_symbols(sexp, allow_keyword=True):
    if sexp.nullp():
        return to_sexp_f((Type.CONS, []))

    if sexp.listp():
        if sexp.first().listp():
            allow_keyword = True
        v0 = disassemble_to_symbols(sexp.first(), allow_keyword=allow_keyword)
        v1 = disassemble_to_symbols(sexp.rest(), allow_keyword=False)
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
    symbols = disassemble_to_symbols(sexp, allow_keyword=False)
    return write_tokens(symbols)


def assemble(s):
    symbols = read_tokens(s)
    return assemble_from_symbols(symbols)
