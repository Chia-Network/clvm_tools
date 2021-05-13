from typing import List

import pathlib

from ir.reader import read_ir
from ir.writer import write_ir_to_stream

from clvm.chia_dialect import chia_dialect_with_op_table
from clvm.dialect import Dialect, DialectInfo
from clvm.handle_unknown_op import handle_unknown_op_strict
from clvm.EvalError import EvalError

from clvm_tools.binutils import assemble_from_ir, disassemble_to_ir

from .compile import make_do_com
from .optimize import make_do_opt


def do_read(args, max_cost):
    filename = args.first().as_atom()
    s = open(filename).read()
    ir_sexp = args.to(read_ir(s))
    sexp = assemble_from_ir(ir_sexp)
    return 1, sexp


def do_write(args, max_cost):
    filename = args.first().as_atom()
    data = args.rest().first()
    with open(filename, "w") as f:
        write_ir_to_stream(disassemble_to_ir(data), f)
    return 1, args.to(0)


def dialect_for_search_paths(search_paths: List[str], strict: bool) -> DialectInfo:
    dialect = chia_dialect_with_op_table(strict)

    def do_full_path_for_name(args, max_cost):
        filename = args.first().as_atom()
        for path in search_paths:
            f_path = pathlib.Path(path) / bytes(filename).decode()
            if f_path.is_file():
                return 1, args.to(str(f_path).encode())
        raise EvalError("can't open %s" % filename, args)

    def run_program(program, args):
        return dialect.run_program(program, args, max_cost=int(1e15), pre_eval_f=None, to_python=program.to)

    BINDINGS = {
        b"com": make_do_com(run_program),
        b"opt": make_do_opt(run_program),
        b"_full_path_for_name": do_full_path_for_name,
        b"_read": do_read,
        b"_write": do_write,
    }

    dialect.update(BINDINGS)
    return dialect
