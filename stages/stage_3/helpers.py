import pathlib

from ir.reader import read_ir
from ir.writer import write_ir


from clvm.EvalError import EvalError

from clvm.runtime_001 import OPERATOR_LOOKUP as ORIGINAL_OPERATOR_LOOKUP

from ir.Type import Type
from ir.utils import (
    ir_new,
    ir_val,
    ir_as_atom,
)

from clvm_tools.binutils import assemble_from_ir

from clvm_tools.NodePath import NodePath

from .codegen import do_codegen
from .mod import do_compile_lambda


# for debugging brevity
wi = write_ir


OPERATOR_LOOKUP = dict(ORIGINAL_OPERATOR_LOOKUP)


def do_com(args):
    return 1, args


def do_assemble(args):
    r = assemble_from_ir(args.first())
    return 1, ir_new(Type.CODE, r)


def do_node_index_to_path(args):
    v = ir_val(args.first()).as_int()
    r = args.to(NodePath(v).as_path())
    return 1, r


def do_read_ir(args):
    filename = ir_as_atom(args.first())
    s = open(filename).read()
    ir_sexp = read_ir(s, args.to)
    return 1, ir_sexp


OPERATOR_LOOKUP[b"com"] = do_com
OPERATOR_LOOKUP[b"_assemble"] = do_assemble
OPERATOR_LOOKUP[b"_compile_lambda"] = do_compile_lambda
OPERATOR_LOOKUP[b"_node_index_to_path"] = do_node_index_to_path
OPERATOR_LOOKUP[b"_read_ir"] = do_read_ir
OPERATOR_LOOKUP[b"_codegen"] = do_codegen


def operators_for_context(search_paths):
    operator_lookup = dict(OPERATOR_LOOKUP)

    def do_full_path_for_name(args):
        filename = ir_as_atom(args.first()).decode()
        for path in search_paths:
            f_path = pathlib.Path(path) / filename
            if f_path.is_file():
                return 1, args.to(ir_new(Type.SYMBOL, str(f_path).encode()))
        raise EvalError("can't open %s" % filename, args)

    operator_lookup[b"_full_path_for_name"] = do_full_path_for_name
    return operator_lookup
