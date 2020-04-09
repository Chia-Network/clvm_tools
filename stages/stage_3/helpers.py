from clvm import run_program as original_run_program

from clvm.runtime_001 import OPERATOR_LOOKUP as ORIGINAL_OPERATOR_LOOKUP

OPERATOR_LOOKUP = dict(ORIGINAL_OPERATOR_LOOKUP)


def run_program(*args, **kwargs):
    return original_run_program(*args, **kwargs, operator_lookup=OPERATOR_LOOKUP)


def do_blop(args):
    breakpoint()
    return 1, args


OPERATOR_LOOKUP[b"blop"] = do_blop
