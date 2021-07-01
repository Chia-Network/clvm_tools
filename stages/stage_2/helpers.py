from clvm import KEYWORD_TO_ATOM
from clvm_tools.NodePath import TOP


QUOTE_ATOM = KEYWORD_TO_ATOM["q"]
APPLY_ATOM = KEYWORD_TO_ATOM["a"]


def quote(sexp):
    """quoted list as a python list, not as an sexp"""
    return (QUOTE_ATOM, sexp)


def eval(prog, args):
    return prog.to([APPLY_ATOM, prog, args])


def run(prog, macro_lookup):
    """
    PROG => (e (com (q . PROG) (mac)) ARGS)

    The result can be evaluated with the stage_com eval
    function.
    """
    args = TOP.as_path()
    mac = quote(macro_lookup)
    return eval(prog.to([b"com", prog, mac]), args)


def brun(prog, args):
    return eval(prog.to(quote(prog)), quote(args))
