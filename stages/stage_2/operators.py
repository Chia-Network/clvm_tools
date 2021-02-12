import pathlib

from ir.reader import read_ir
from ir.writer import write_ir_to_stream


from clvm.EvalError import EvalError
from clvm_tools.operator_dict import OperatorDict

from clvm_tools.binutils import assemble_from_ir, disassemble_to_ir

from stages.stage_0 import (
    run_program as run_program_0,
    OPERATOR_LOOKUP as ORIGINAL_OPERATOR_LOOKUP,
)

from .compile import make_do_com
from .optimize import make_do_opt


def do_read(args):
    filename = args.first().as_atom()
    s = open(filename).read()
    ir_sexp = args.to(read_ir(s))
    sexp = assemble_from_ir(ir_sexp)
    return 1, sexp


def do_write(args):
    filename = args.first().as_atom()
    data = args.rest().first()
    with open(filename, "w") as f:
        write_ir_to_stream(disassemble_to_ir(data), f)
    return 1, args.to(0)


def run_program_for_search_paths(search_paths):

    def do_full_path_for_name(args):
        filename = args.first().as_atom()
        for path in search_paths:
            f_path = pathlib.Path(path) / bytes(filename).decode()
            if f_path.is_file():
                return 1, args.to(str(f_path).encode())
        raise EvalError("can't open %s" % filename, args)

    operator_lookup = OperatorDict(ORIGINAL_OPERATOR_LOOKUP)

    def run_program(
        program, args, operator_lookup=operator_lookup, max_cost=None, pre_eval_f=None, strict=False
    ):
        return run_program_0(
            program,
            args,
            operator_lookup=operator_lookup,
            max_cost=max_cost,
            pre_eval_f=pre_eval_f,
            strict=strict
        )

    BINDINGS = {
        b"com": make_do_com(run_program),
        b"opt": make_do_opt(run_program),
        b"_full_path_for_name": do_full_path_for_name,
        b"_read": do_read,
        b"_write": do_write,
    }

    operator_lookup.update(BINDINGS)

    return run_program
