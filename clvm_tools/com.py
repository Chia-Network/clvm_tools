import argparse
import io
import pathlib
import pkg_resources
import sys

from clvm import to_sexp_f, run_program
from clvm.EvalError import EvalError

from clvm_tools.clvmc import load_clvm

from ir import reader

from . import binutils, patch_sexp  # noqa

from stages.stage_3.helpers import operators_for_context


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
        "-t",
        "--use-ir",
        action="store_true",
        help="use tagged IR mode for data",
        default=False,
    )
    parser.add_argument(
        "-i",
        "--include",
        type=pathlib.Path,
        help="add a search path for included files",
        action="append",
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

    clvm_source = pkg_resources.resource_filename("stages", "stage_3.clvm")
    prog = load_clvm(clvm_source, to_sexp_f)

    src_text = args.path_or_code
    data = reader.read_ir(src_text)
    if not args.use_ir:
        data = binutils.assemble_from_ir(data)

    operator_lookup = operators_for_context(args.include)

    try:
        cost, r = run_program(prog, data, operator_lookup=operator_lookup)
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
