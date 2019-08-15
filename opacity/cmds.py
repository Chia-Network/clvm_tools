import argparse
import binascii
import hashlib
import importlib
import io
import sys

from clvm import to_sexp_f
from clvm.EvalError import EvalError
from clvm.serialize import sexp_from_stream, sexp_to_stream

from opacity import binutils

from ir import reader

from .debug import make_tracing_f, trace_to_text


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
        description='Compile an opacity script.'
    )
    parser.add_argument(
        "-H", "--script_hash", action="store_true",
        help="Show sha256 script hash")
    parser.add_argument(
        "path_or_code", nargs="*", type=path_or_code,
        help="path to opacity script, or literal script")

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
        print(binascii.hexlify(compiled_script).decode())


def opd(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Disassemble a compiled opacity script.'
    )
    parser.add_argument(
        "script", nargs="+", type=binascii.unhexlify,
        help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    for blob in args.script:
        sexp = sexp_from_stream(io.BytesIO(blob), to_sexp_f)
        print(binutils.disassemble(sexp))


def stage_import(stage):
    stage_path = "stage_%s" % stage
    try:
        return importlib.import_module(stage_path)
    except ImportError:
        raise ValueError("bad stage: %s" % stage)


def as_bin(streamer_f):
    f = io.BytesIO()
    streamer_f(f)
    return f.getvalue()


def run(args=sys.argv):
    return brun_or_run(args, is_run=True)


def brun(args=sys.argv):
    return brun_or_run(args)


def brun_or_run(args, is_run=False):
    parser = argparse.ArgumentParser(
        description='Execute a clvm script.'
    )
    parser.add_argument(
        "-s", "--stage", type=stage_import,
        help="stage number to include", default=stage_import(0))
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Display resolve of all reductions, for debugging")
    parser.add_argument(
        "-d", "--dump", action="store_true",
        help="dump hex version of final output")
    parser.add_argument(
        "path_or_code", type=path_or_code,
        help="path to clvm script, or literal script")
    parser.add_argument(
        "args", type=reader.read_ir, help="arguments", nargs="?",
        default=reader.read_ir("()"))

    args = parser.parse_args(args=args[1:])

    eval_f = args.stage.EVAL_F

    src_text = args.path_or_code
    src_sexp = reader.read_ir(src_text)
    assembled_sexp = binutils.assemble_from_ir(src_sexp)

    if args.verbose:

        def transform_exception(ex):
            return to_sexp_f(("FAIL: %s" % str(ex)).encode("utf8"))

        eval_f, log_entries = make_tracing_f(eval_f, transform_exception)

    run_script = args.stage.run if is_run else args.stage.brun

    try:
        env = binutils.assemble_from_ir(args.args)
        input_sexp = to_sexp_f((assembled_sexp, env))
        result = eval_f(eval_f, run_script, input_sexp)
        if args.dump:
            blob = as_bin(lambda f: sexp_to_stream(result, f))
            output = binascii.hexlify(blob).decode("utf8")
        else:
            output = binutils.disassemble(result)
    except EvalError as ex:
        output = "FAIL: %s %s" % (ex, binutils.disassemble(ex._sexp))
        result = ex._sexp
        return -1
    except Exception as ex:
        result = src_sexp
        output = str(ex)
        raise
    finally:
        if args.verbose:
            trace_to_text(log_entries, binutils.disassemble)
        else:
            print(output)


def read_ir(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Read script and tokenize to IR.'
    )
    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    sexp = reader.read_ir(args.script)
    blob = stream_to_bin(lambda f: sexp_to_stream(sexp, f))
    print(binascii.hexlify(blob).decode())


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
