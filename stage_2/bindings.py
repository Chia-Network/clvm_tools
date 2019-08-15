from clvm import eval_f, to_sexp_f
from opacity import binutils

from opacity.patch_eval_f import bind_eval_f, wrap_eval_f

from .expand import expand_sexp, DEFAULT_MACROS_DEFINITIONS

from .lambda_ import (
    do_defmacro_op, do_lambda_op,
    symbol_replace, symbol_table_sexp
)
from .mod import do_mod_op
from .qa import qa_sexp
from .qq import compile_qq_sexp


def do_expand_op(args, eval_f):
    if len(args.as_python()) not in (1, 2):
        raise SyntaxError("require 1 or 2 arguments to expand")
    macro_lookup = args.rest()
    if not macro_lookup.nullp():
        macro_lookup = macro_lookup.first()
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


def make_eval_f(function_bindings, macro_bindings):
    def qa_transformer(sexp, env, eval_f):
        return qa_sexp(expand_sexp(sexp, macro_bindings, eval_f)), env

    return wrap_eval_f(bind_eval_f(eval_f, function_bindings), qa_transformer)


BINDINGS = {
    "expand_op": do_expand_op,
    "list": do_list,
    "qa_op": do_qa_op,
    "compile_qq_op": do_compile_qq_op,
    "map": do_map,
    "symbol_table": do_symbol_table,
    "symbol_replace": do_symbol_replace,
    "lambda_op": do_lambda_op,
    "defmacro_op": do_defmacro_op,
    "mod_op": do_mod_op,
}


def make_macro_built_ins(function_bindings, macros):
    built_ins_list = []
    null = to_sexp_f([])
    for macro in macros:
        eval_f = make_eval_f(function_bindings, to_sexp_f(built_ins_list))
        macro_sexp = binutils.assemble(macro)
        macro_binding = eval_f(eval_f, macro_sexp, null)
        built_ins_list.append(macro_binding)
    return to_sexp_f(built_ins_list)


MACRO_BUILT_INS = make_macro_built_ins(
    BINDINGS, DEFAULT_MACROS_DEFINITIONS)

EVAL_F = make_eval_f(BINDINGS, MACRO_BUILT_INS)

brun = run = binutils.assemble("(e (f (a)) (r (a)))")
