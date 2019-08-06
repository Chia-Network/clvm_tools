from clvm import eval_f, to_sexp_f

from ..patch_eval_f import bind_eval_f, wrap_eval_f

from .expand import expand_sexp, DEFAULT_MACRO_LOOKUP
from .lambda_ import do_lambda_op, symbol_replace, symbol_table_sexp
from .qa import qa_sexp
from .qq import compile_qq_sexp


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


def do_compile_qq_op(args, eval_f):
    if len(args.as_python()) != 1:
        raise SyntaxError("require 1 argument to qq")
    return compile_qq_sexp(args.first())


def do_list(args, eval_f):
    return args


def do_map(args, eval_f):
    if len(args.as_python()) != 2:
        raise SyntaxError("require 2 arguments to map")
    r = []
    for sexp in args.rest().first().as_iter():
        r.append(eval_f(eval_f, args.first(), to_sexp_f(sexp)))
    return to_sexp_f(r)


def do_symbol_table(args, eval_f):
    return symbol_table_sexp(args.first())


def do_symbol_replace(args, eval_f):
    return symbol_replace(args.first(), args.rest().first())


def qa_transformer(sexp, env, eval_f):
    return qa_sexp(expand_sexp(sexp, DEFAULT_MACRO_LOOKUP, eval_f)), env


BINDINGS = {
    "expand_op": do_expand_op,
    "list": do_list,
    "qa_op": do_qa_op,
    "compile_qq_op": do_compile_qq_op,
    "map": do_map,
    "symbol_table": do_symbol_table,
    "symbol_replace" : do_symbol_replace,
    "lambda_op": do_lambda_op,
}


EVAL_F = wrap_eval_f(bind_eval_f(eval_f, BINDINGS), qa_transformer)
