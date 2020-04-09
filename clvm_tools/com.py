import argparse
import io
import pkg_resources
import sys

from clvm import to_sexp_f
from clvm.EvalError import EvalError
from clvm.serialize import sexp_from_stream, sexp_to_stream

from ir import reader

from . import binutils, patch_sexp  # noqa

from stages.stage_3.helpers import run_program


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


def com(args=sys.argv):
    parser = argparse.ArgumentParser(description="Execute a clvm script.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display resolve of all reductions, for debugging",
    )
    parser.add_argument("-c", "--cost", action="store_true", help="Show cost")
    parser.add_argument("-m", "--max-cost", type=int, help="Maximum cost")
    parser.add_argument(
        "-d", "--dump", action="store_true", help="dump hex version of final output"
    )
    parser.add_argument(
        "path_or_code", type=path_or_code, help="path to clvm script, or literal script"
    )
    parser.add_argument(
        "args",
        type=reader.read_ir,
        help="arguments",
        nargs="?",
        default=reader.read_ir("()"),
    )

    args = parser.parse_args(args=args[1:])

    blob_hex_path = pkg_resources.resource_filename("stages", "stage_3.clvm.hex")
    blob_hex = open(blob_hex_path).read()
    blob = bytes.fromhex(blob_hex)

    prog = sexp_from_stream(io.BytesIO(blob), to_sexp_f)

    src_text = args.path_or_code
    src_sexp = reader.read_ir(src_text)
    data = to_sexp_f(src_sexp)

    try:
        cost, r = run_program(prog, data)
    except EvalError as ex:
        r = f"failed: {ex} {ex._sexp}"

    print(r)
    from ir import writer

    r1 = writer.write_ir(r)
    print(r1)


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
