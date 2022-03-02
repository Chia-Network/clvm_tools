import argparse
import sys
from clvm import to_sexp_f, KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, SExp
from clvm.EvalError import EvalError
from clvm.serialize import sexp_to_stream
from clvm_rs import run_chia_program, MEMPOOL_MODE
from .cmds import path_or_code, as_bin

from ir import reader
from . import binutils

def brun(args=sys.argv):
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
        "-c", "--cost", action="store_true", help="Show cost")
    parser.add_argument(
        "-m", "--max-cost", type=int, default=11000000000, help="Maximum cost")
    parser.add_argument(
        "-d", "--dump", action="store_true",
        help="dump hex version of final output")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress printing the program result")
    parser.add_argument("--backend", type=str, help="force use of 'rust' or 'python' backend")
    parser.add_argument(
        "path_or_code", type=path_or_code,
        help="filepath to clvm script, or a literal script")

    parser.add_argument(
        "env", nargs="?", type=path_or_code,
        help="clvm script environment, as clvm src, or hex")

    args = parser.parse_args(args=args[1:])

    input_program = None
    input_args = None

    if args.hex:
        input_program = bytes.fromhex(args.path_or_code)
        if args.env:
            input_args = bytes.fromhex(args.env)
        else:
            input_args = b"\x80"
    else:
        src_text = args.path_or_code
        try:
            src_sexp = reader.read_ir(src_text)
        except SyntaxError as ex:
            print("FAIL: %s" % (ex))
            return -1
        assembled_sexp = binutils.assemble_from_ir(src_sexp)
        if args.env:
            env_ir = reader.read_ir(args.env)
            env = binutils.assemble_from_ir(env_ir)
            input_args = env.as_bin()
        else:
            input_args = b"\x80"

        input_program = assembled_sexp.as_bin()

    cost = 0
    try:
        output = "(didn't finish)"
        max_cost = max(0, args.max_cost)

        cost, result = run_chia_program(
            input_program,
            input_args,
            max_cost,
            MEMPOOL_MODE if (args.mempool or args.strict) else 0,
        )
        result = SExp.to(result)

        if args.cost:
            print("cost = %d" % cost)
        if args.dump:
            blob = as_bin(lambda f: sexp_to_stream(result, f))
            output = blob.hex()
        elif args.quiet:
            output = ''
        else:
            output = binutils.disassemble(result)
    except EvalError as ex:
        result = to_sexp_f(ex._sexp)
        output = "FAIL: %s %s" % (ex, binutils.disassemble(result))
        return -1
    except Exception as ex:
        output = str(ex)
        raise
    finally:
        print(output)

