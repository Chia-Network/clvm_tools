from clvm import casts
from clvm import to_sexp_f

from .expand import expand_sexp
from .qa import qa_sexp


def do_expand(args, eval_f):
    if len(args.as_python()) not in (1, 2):
        raise SyntaxError("require 1 or 2 arguments to expand")
    val = casts.int_from_bytes(args.first().as_atom())
    return to_sexp_f(val * val)


def do_qa(args, eval_f):
    if len(args.as_python()) != 1:
        raise SyntaxError("require 1 argument to qa")
    return qa_sexp(args.first())


BINDINGS = {
    "expand": do_expand,
    "qa": do_qa,
}
