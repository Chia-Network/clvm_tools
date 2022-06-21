import argparse
import importlib
import io
import json
import pathlib
import sys
import time

from clvm import to_sexp_f, KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, SExp
import clvm_tools_rs
from clvm.EvalError import EvalError
from clvm.serialize import sexp_from_stream, sexp_to_stream
from clvm.operators import OP_REWRITE

from ir import reader

from . import binutils
from .debug import make_trace_pre_eval, trace_to_text, trace_to_table
from .sha256tree import sha256tree

try:
    from clvm_rs import run_chia_program, MEMPOOL_MODE
except ImportError:
    run_chia_program = None


def path_or_code(arg):
    try:
        with open(arg) as f:
            return f.read()
    except IOError:
        return arg


def stream_to_bin(write_f):
    b = io.BytesIO()
    write_f(b)
    return b.getvalue()


def call_tool(tool_name, desc, conversion, input_args):
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "-H", "--script-hash", action="store_true", help="Show only sha256 tree hash of program"
    )
    parser.add_argument(
        "path_or_code",
        nargs="*",
        type=path_or_code,
        help="path to clvm script, or literal script",
    )

    sys.setrecursionlimit(20000)
    args = parser.parse_args(args=input_args[1:])

    for program in args.path_or_code:
        if program == "-":
            program = sys.stdin.read()
        sexp, text = conversion(program)
        if args.script_hash:
            print(sha256tree(sexp).hex())
        elif text:
            print(text)


def opc(args=sys.argv):
    def conversion(text):
        try:
            ir_sexp = reader.read_ir(text)
            sexp = binutils.assemble_from_ir(ir_sexp)
        except SyntaxError as ex:
            print("%s" % ex.msg)
            return None, None
        return sexp, sexp.as_bin().hex()

    call_tool("opc", "Compile a clvm script.", conversion, args)


def opd(args=sys.argv):
    def conversion(blob):
        sexp = sexp_from_stream(io.BytesIO(bytes.fromhex(blob)), to_sexp_f)
        return sexp, binutils.disassemble(sexp)
    call_tool("opd", "Disassemble a compiled clvm script from hex.", conversion, args)


def stage_import(stage):
    stage_path = "stages.stage_%s" % stage
    try:
        return importlib.import_module(stage_path)
    except ImportError:
        raise ValueError("bad stage: %s" % stage)


def as_bin(streamer_f):
    f = io.BytesIO()
    streamer_f(f)
    return f.getvalue()


def run(args=sys.argv):
    sys.stdout.write(bytes(clvm_tools_rs.launch_tool("run", args, 2)).decode('utf8'))

def brun(args=sys.argv):
    return launch_tool(args, "brun")


def launch_tool(args, tool_name, default_stage=0):
    sys.setrecursionlimit(20000)
    parser = argparse.ArgumentParser(
        description='Execute a clvm script.'
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="deprecated alias for --mempool")
    parser.add_argument(
        "--mempool", action="store_true",
        help="Unknown opcodes are always fatal errors in mempool mode")
    parser.add_argument(
        "-x", "--hex", action="store_true",
        help="Read program and environment as hexadecimal bytecode")
    parser.add_argument(
        "-s", "--stage", type=stage_import,
        help="stage number to include", default=stage_import(default_stage))
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Display resolve of all reductions, for debugging")
    parser.add_argument(
        "-t", "--table", action="store_true",
        help="Print diagnostic table of reductions, for debugging")
    parser.add_argument(
        "-c", "--cost", action="store_true", help="Show cost")
    parser.add_argument(
        "--time", action="store_true", help="Print execution time")
    parser.add_argument(
        "-m", "--max-cost", type=int, default=11000000000, help="Maximum cost")
    parser.add_argument(
        "-d", "--dump", action="store_true",
        help="dump hex version of final output")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress printing the program result")
    parser.add_argument(
        "-y", "--symbol-table", type=pathlib.Path,
        help=".SYM file generated by compiler")
    parser.add_argument(
        "-n", "--no-keywords", action="store_true",
        help="Output result as data, not as a program")
    parser.add_argument("--backend", type=str, help="force use of 'rust' or 'python' backend")
    parser.add_argument(
        "-i",
        "--include",
        type=pathlib.Path,
        help="add a search path for included files",
        action="append",
        default=[],
    )
    parser.add_argument(
        "path_or_code", type=path_or_code,
        help="filepath to clvm script, or a literal script")

    parser.add_argument(
        "env", nargs="?", type=path_or_code,
        help="clvm script environment, as clvm src, or hex")

    args = parser.parse_args(args=args[1:])

    keywords = {} if args.no_keywords else KEYWORD_FROM_ATOM

    if hasattr(args.stage, "run_program_for_search_paths"):
        run_program = args.stage.run_program_for_search_paths(args.include)
    else:
        run_program = args.stage.run_program

    program_serialized = None
    arg_serialized = None

    time_start = time.perf_counter()
    if args.hex:
        program_serialized = bytes.fromhex(args.path_or_code)
        if not args.env:
            args.env = "80"
        arg_serialized = bytes.fromhex(args.env)
        time_read_hex = time.perf_counter()

    else:

        src_text = args.path_or_code
        try:
            src_sexp = reader.read_ir(src_text)
        except SyntaxError as ex:
            print("FAIL: %s" % (ex))
            return -1
        program_serialized = binutils.assemble_from_ir(src_sexp).as_bin()
        if not args.env:
            args.env = "()"
        env_ir = reader.read_ir(args.env)
        arg_serialized = binutils.assemble_from_ir(env_ir).as_bin()

        time_assemble = time.perf_counter()

    pre_eval_f = None
    symbol_table = None

    log_entries = []

    if args.symbol_table:
        with open(args.symbol_table) as f:
            symbol_table = json.load(f)
        pre_eval_f = make_trace_pre_eval(log_entries, symbol_table)
    elif args.verbose or args.table:
        pre_eval_f = make_trace_pre_eval(log_entries)

    if hasattr(args.stage, tool_name):
        arg_serialized = b"\xff" + program_serialized + arg_serialized
        program_serialized = getattr(args.stage, tool_name).as_bin()

    cost = 0
    try:
        output = "(didn't finish)"

        use_rust = (
            (tool_name != "run")
            and not pre_eval_f
            and (
                args.backend == "rust"
                or (run_chia_program and args.backend != "python")
            )
            and args.stage == 0
        )
        max_cost = args.max_cost
        if use_rust:
            time_parse_input = time.perf_counter()

            cost, result = run_chia_program(
                program_serialized,
                arg_serialized,
                max_cost,
                MEMPOOL_MODE if (args.mempool or args.strict) else 0,
            )
            time_done = time.perf_counter()
            result = SExp.to(result)
        else:
            program = sexp_from_stream(io.BytesIO(program_serialized), to_sexp_f)
            arg = sexp_from_stream(io.BytesIO(arg_serialized), to_sexp_f)

            time_parse_input = time.perf_counter()
            cost, result = run_program(
                program, arg, max_cost=max_cost, pre_eval_f=pre_eval_f, strict=args.mempool | args.strict)
            time_done = time.perf_counter()
        if args.cost:
            print("cost = %d" % cost)
        if args.time:
            if args.hex:
                print('read_hex: %f' % (time_read_hex - time_start))
            else:
                print('assemble_from_ir: %f' % (time_assemble - time_start))
                print('to_sexp_f: %f' % (time_parse_input - time_assemble))
            print('run_program: %f' % (time_done - time_parse_input))
        if args.dump:
            blob = as_bin(lambda f: sexp_to_stream(result, f))
            output = blob.hex()
        elif args.quiet:
            output = ''
        else:
            output = binutils.disassemble(result, keywords)
    except EvalError as ex:
        result = to_sexp_f(ex._sexp)
        output = "FAIL: %s %s" % (ex, binutils.disassemble(result, keywords))
        return -1
    except Exception as ex:
        output = str(ex)
        raise
    finally:
        print(output)
        if args.verbose or symbol_table:
            print()
            trace_to_text(log_entries, binutils.disassemble, symbol_table)
        if args.table:
            trace_to_table(log_entries, binutils.disassemble, symbol_table)


def read_ir(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Read script and tokenize to IR.'
    )
    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    sexp = reader.read_ir(args.script)
    blob = stream_to_bin(lambda f: sexp_to_stream(sexp, f))
    print(blob.hex())


"""
Copyright 2018 Chia Network Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
