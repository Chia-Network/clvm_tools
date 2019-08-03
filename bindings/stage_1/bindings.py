from clvm import eval_f

from ..patch_eval_f import bind_eval_f, wrap_eval_f

from .expand import expand_sexp, DEFAULT_MACRO_LOOKUP
from .qa import qa_sexp
from .qq import qq_sexp


def do_expand_op(args, eval_f):
    if len(args.as_python()) not in (1, 2):
        raise SyntaxError("require 1 or 2 arguments to expand")
    macro_lookup = args.rest()
    if macro_lookup.nullp():
        macro_lookup = DEFAULT_MACRO_LOOKUP
    return expand_sexp(args.first(), macro_lookup, eval_f)


def do_qa_op(args, eval_f):
    if len(args.as_python()) != 1:
        raise SyntaxError("require 1 argument to qa")
    return qa_sexp(args.first())


def do_qq_op(args, eval_f):
    if len(args.as_python()) != 1:
        raise SyntaxError("require 1 argument to qq")
    qquoted_sexp = qq_sexp(args.first())
    r = eval_f(eval_f, qquoted_sexp, args.null())
    return r


def do_list(args, eval_f):
    return args


def qa_transformer(sexp, env, eval_f):
    return qa_sexp(expand_sexp(sexp, DEFAULT_MACRO_LOOKUP, eval_f)), env


BINDINGS = {
    "expand_op": do_expand_op,
    "list": do_list,
    "qa_op": do_qa_op,
    "qq_op": do_qq_op,
}


EVAL_F = wrap_eval_f(bind_eval_f(eval_f, BINDINGS), qa_transformer)
