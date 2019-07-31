import argparse
import binascii
import hashlib
import importlib
import io
import sys

from clvm import eval_f, to_sexp_f
from clvm.EvalError import EvalError
from clvm.serialize import sexp_from_stream

from opacity.binutils import assemble_from_symbols, disassemble

from ir import reader

from .debug import trace_to_html, trace_to_text



def path_or_code(arg):
    try:
        with open(arg) as f:
            return f.read()
    except IOError:
        return arg


def opc(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Compile an opacity script.'
    )
    parser.add_argument("-H", "--script_hash", action="store_true", help="Show sha256 script hash")
    parser.add_argument(
        "path_or_code", nargs="*", type=path_or_code, help="path to opacity script, or literal script")

    args = parser.parse_args(args=args[1:])

    for text in args.path_or_code:
        try:
            ir_sexp = reader.read_tokens(text)
            sexp = assemble_from_symbols(ir_sexp)
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
        "script", nargs="+", type=binascii.unhexlify, help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    for blob in args.script:
        sexp = sexp_from_stream(io.BytesIO(blob), to_sexp_f)
        print(disassemble(sexp))


def brun(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Run a clvm script.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")
    parser.add_argument(
        "solution", nargs="?", help="solution in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])
    args.debug = 0

    read_sexp = reader.read_tokens(args.script)
    sexp = assemble_from_symbols(read_sexp)

    solution = sexp.null()
    if args.solution:
        tokens = reader.read_tokens(args.solution)
        solution = assemble_from_symbols(tokens)
    do_reduction(args, sexp, solution)


def do_reduction(args, sexp, solution):
    the_log = []
    local_eval_f = eval_f

    if args.verbose:
        original_eval_f = eval_f
        def debug_eval_f(eval_f, sexp, args):
            row = [(sexp, args), sexp.null()]
            the_log.append(row)
            r = original_eval_f(eval_f, sexp, args)
            row[-1] = r
            return r
        local_eval_f = debug_eval_f

    try:
        reductions = local_eval_f(local_eval_f, sexp, solution)
        output = disassemble(reductions)
    except EvalError as e:
        output = "FAIL: %s %s" % (e, disassemble(e._sexp))
        result = e._sexp
        return -1
    except Exception as e:
        output = "EXCEPTION: %r" % e
        raise
    finally:
        if not args.debug:
            print(output)

        # TODO solve the debugging problem
        if args.debug:
            trace_to_html(the_log, disassemble)
        elif args.verbose:
            trace_to_text(the_log, disassemble)


def rewrite(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Rewrite an opacity program in terms of the core language.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    sexp = assemble_from_symbols(reader.read_tokens("(expand %s)" % args.script))
    solution = sexp.null()
    do_reduction(args, sexp, solution)


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
