from clvm.EvalError import EvalError

from ir.Type import Type
from ir.utils import (
    ir_new,
    ir_cons,
    ir_null,
    ir_type,
    ir_list,
    ir_offset,
    ir_val,
    ir_nullp,
    ir_listp,
    ir_as_sexp,
    ir_is_atom,
    ir_as_atom,
    ir_as_int,
    ir_first,
    ir_rest,
)

from clvm_tools.NodePath import NodePath, LEFT, RIGHT, TOP


from clvm.runtime_001 import KEYWORD_TO_ATOM


CONS = KEYWORD_TO_ATOM["c"]
QUOTE = KEYWORD_TO_ATOM["q"]


def ir_flatten(ir_sexp, filter=lambda x: ir_type(x) == Type.SYMBOL):
    if ir_listp(ir_sexp):
        return ir_flatten(ir_first(ir_sexp)) + ir_flatten(ir_rest(ir_sexp))
    if filter(ir_sexp):
        return [ir_val(ir_sexp).as_atom()]
    return []
