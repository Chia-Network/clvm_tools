from clvm import run_program as original_run_program

from clvm.runtime_001 import OPERATOR_LOOKUP as ORIGINAL_OPERATOR_LOOKUP

from ir.Type import Type
from ir.utils import (
    ir_new,
    ir_cons,
    ir_null,
    ir_type,
    ir_offset,
    ir_val,
    ir_nullp,
    ir_listp,
    ir_as_sexp,
    ir_is_atom,
    ir_as_atom,
    ir_first,
    ir_rest,
    ir_symbol,
    ir_as_symbol,
    ir_iter,
)

from clvm_tools.binutils import assemble_from_ir


OPERATOR_LOOKUP = dict(ORIGINAL_OPERATOR_LOOKUP)


def run_program(*args, **kwargs):
    return original_run_program(*args, **kwargs, operator_lookup=OPERATOR_LOOKUP)


def do_com(args):
    return 1, args


def do_assemble(args):
    r = assemble_from_ir(args.first())
    return 1, ir_new(Type.CODE, r)


OPERATOR_LOOKUP[b"com"] = do_com
OPERATOR_LOOKUP[b"assemble"] = do_assemble
