import argparse
import hashlib
import importlib
import io
import json
import pathlib
import sys
import time

from clvm import to_sexp_f
from clvm.EvalError import EvalError
from clvm.serialize import sexp_from_stream, sexp_to_stream
from clvm import KEYWORD_FROM_ATOM

from ir import reader

from . import binutils
from .debug import make_trace_pre_eval, trace_to_text, trace_to_table

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


def opc(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Compile a clvm script.'
    )
    parser.add_argument(
        "-H", "--script_hash", action="store_true",
        help="Show sha256 script hash")
    parser.add_argument(
        "path_or_code", nargs="*", type=path_or_code,
        help="path to clvm script, or literal script")

    args = parser.parse_args(args=args[1:])

    for text in args.path_or_code:
        try:
            ir_sexp = reader.read_ir(text)
            sexp = binutils.assemble_from_ir(ir_sexp)
        except SyntaxError as ex:
            print("%s" % ex.msg)
            continue
        compiled_script = sexp.as_bin()
        if args.script_hash:
            print(hashlib.sha256(compiled_script).hexdigest())
        print(compiled_script.hex())


def opd(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Disassemble a compiled clvm script.'
    )
    parser.add_argument(
        "script", nargs="+", type=bytes.fromhex,
        help="hex version of clvm script")
    args = parser.parse_args(args=args[1:])

    for blob in args.script:
        sexp = sexp_from_stream(io.BytesIO(blob), to_sexp_f)
        print(binutils.disassemble(sexp))


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
    return launch_tool(args, "run", default_stage=2)


def brun(args=sys.argv):
    return launch_tool(args, "brun")


def launch_tool(args, tool_name, default_stage=0):
    sys.setrecursionlimit(20000)
    parser = argparse.ArgumentParser(
        description='Execute a clvm script.'
    )
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
        "-m", "--max-cost", type=int, help="Maximum cost")
    parser.add_argument(
        "-d", "--dump", action="store_true",
        help="dump hex version of final output")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress printing the program result")
    parser.add_argument(
        "-y", "--symbol-table", type=pathlib.Path,
        help=".SYM file generated by compiler")
    parser.add_argument("-n", "--no-keywords", action="store_true",
        help="Output result as data, not as a program")
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
        help="path to clvm script, or literal script")
    parser.add_argument(
        "args", type=reader.read_ir, help="arguments", nargs="?",
        default=reader.read_ir("()"))

    args = parser.parse_args(args=args[1:])

    keywords = {} if args.no_keywords else KEYWORD_FROM_ATOM

    if hasattr(args.stage, "run_program_for_search_paths"):
        run_program = args.stage.run_program_for_search_paths(args.include)
    else:
        run_program = args.stage.run_program

    src_text = args.path_or_code
    try:
        src_sexp = reader.read_ir(src_text)
    except SyntaxError as ex:
        print("FAIL: %s" % (ex))
        return -1
    assembled_sexp = binutils.assemble_from_ir(src_sexp)

    pre_eval_f = None
    symbol_table = None

    log_entries = []

    if args.symbol_table:
        with open(args.symbol_table) as f:
            symbol_table = json.load(f)
        pre_eval_f = make_trace_pre_eval(log_entries, symbol_table)
    elif args.verbose or args.table:
        pre_eval_f = make_trace_pre_eval(log_entries)

    run_script = getattr(args.stage, tool_name)

    cost = 0
    try:
        output = "(didn't finish)"
        time_start = time.perf_counter()
        env = binutils.assemble_from_ir(args.args)
        time_assemble = time.perf_counter()
        input_sexp = to_sexp_f((assembled_sexp, env))
        time_parse_input = time.perf_counter()
        cost, result = run_program(
            run_script, input_sexp, max_cost=args.max_cost, pre_eval_f=pre_eval_f)
        time_done = time.perf_counter()
        if args.cost:
            print("cost = %d" % cost)
        if args.time:
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
        result = src_sexp
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
