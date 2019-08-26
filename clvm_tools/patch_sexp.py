from clvm import to_sexp_f

from . import binutils

# monkey-patch SExp
SExp = to_sexp_f([]).__class__
SExp.__str__ = SExp.__repr__ = binutils.disassemble
