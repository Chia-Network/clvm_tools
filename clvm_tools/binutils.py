import string

from clvm import KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM
from clvm.casts import int_from_bytes, int_to_bytes
from clvm.SExp import SExp

from ir.reader import read_ir
from ir.writer import write_ir
from ir.utils import (
    ir_as_symbol, ir_cons, ir_first, ir_listp, ir_null,
    ir_nullp, ir_rest, ir_symbol, ir_val, is_ir, ir_offset
)
from ir.Type import Type

QUOTE_KW = KEYWORD_TO_ATOM.get("q")

def assemble_from_ir(ir_sexp):
    keyword = ir_as_symbol(ir_sexp)
    if keyword:
        if keyword[:1] == "#":
            keyword = keyword[1:]
        atom = KEYWORD_TO_ATOM.get(keyword)
        if atom is not None:
            return ir_sexp.to(atom)
        if True:
            return ir_val(ir_sexp)
        raise SyntaxError(
            "can't parse %s at %s" % (keyword, ir_sexp._offset))

    if not ir_listp(ir_sexp):
        return ir_val(ir_sexp)

    if ir_nullp(ir_sexp):
        return ir_sexp.to([])

    first = ir_first(ir_sexp)
    keyword = ir_as_symbol(first)

    sexp_1 = assemble_from_ir(first)
    sexp_2 = assemble_from_ir(ir_rest(ir_sexp))

    if keyword == "q":
        # This check disallows parsing '(q . x)'
        # Note that '(1 . x)' is allowed
        if not (sexp_2.listp() or sexp_2.null()):
            raise SyntaxError(
                "can't parse quote as first element of cons at %s. Expected '(q %s)'" % (ir_offset(ir_sexp), sexp_2)
            )
        if sexp_2.listp():
            if not sexp_2.rest().nullp():
                raise SyntaxError(
                    f"Quote reqires only one argument, but we got {write_ir(ir_sexp)}"
                )
            # The IR reader reads '(q x)' as [ q [ x  nil ] ]
            # We translate that to [ q  x ]
            sexp_2 = sexp_2.first()
        else:
            raise SyntaxError("quote Expected list")

        r = SExp((sexp_1, sexp_2))
        return r

    return sexp_1.cons(sexp_2)


def type_for_atom(atom) -> Type:
    if len(atom) > 2:
        try:
            v = atom.decode("utf8")
            if all(c in string.printable for c in v):
                return Type.QUOTES
        except UnicodeDecodeError:
            pass
        return Type.HEX
    if int_to_bytes(int_from_bytes(atom)) == atom:
        return Type.INT
    return Type.HEX


def disassemble_to_ir(sexp, keyword_from_atom, allow_keyword=None):
    if is_ir(sexp) and allow_keyword is not False:
        return ir_cons(ir_symbol("ir"), sexp)

    if sexp.listp():
        if sexp.first().listp() or allow_keyword is None:
            allow_keyword = True
        v0 = disassemble_to_ir(sexp.first(), keyword_from_atom, allow_keyword=allow_keyword)
        v1 = disassemble_to_ir(sexp.rest(), keyword_from_atom, allow_keyword=False)
        return ir_cons(v0, v1)

    as_atom = sexp.as_atom()
    if allow_keyword:
        v = keyword_from_atom.get(as_atom)
        if v is not None and v != '.':
            return ir_symbol(v)

    if sexp.nullp():
        return ir_null()

    return sexp.to((type_for_atom(as_atom), as_atom))


def disassemble(sexp, keyword_from_atom=KEYWORD_FROM_ATOM):
    symbols = disassemble_to_ir(sexp, keyword_from_atom=keyword_from_atom)
    return write_ir(symbols)


def assemble(s):
    symbols = read_ir(s)
    return assemble_from_ir(symbols)
