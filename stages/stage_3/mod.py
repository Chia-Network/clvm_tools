import collections

from ir.Type import Type
from ir.utils import (
    ir_new,
    ir_cons,
    ir_null,
    ir_type,
    ir_list,
    ir_offset,
    ir_val,
    ir_nullp,
    ir_listp,
    ir_as_sexp,
    ir_is_atom,
    ir_as_atom,
    ir_first,
    ir_rest,
)

from clvm.EvalError import EvalError
from clvm.runtime_001 import KEYWORD_TO_ATOM

from .symbols import ir_flatten

MAIN_NAME = b""

BUILT_IN_TEXT = "if first rest cons + - * ="

BUILT_INS = set([_.encode() for _ in BUILT_IN_TEXT.split()])


def parse_mod_sexp(declaration_sexp, namespace, functions, constants, macros):
    op = ir_as_atom(ir_first(declaration_sexp))
    name = ir_as_atom(ir_first(ir_rest(declaration_sexp)))
    if name in namespace:
        raise SyntaxError('symbol "%s" redefined' % name.decode())
    namespace.add(name)
    if op == b"defmacro":
        macros.append(declaration_sexp)
    elif op == b"defun":
        functions[name] = ir_rest(ir_rest(declaration_sexp))
    elif op == b"defconstant":
        # TODO: this probably doesn't work right
        constants[name] = ir_as_atom(ir_first(ir_rest(ir_rest(declaration_sexp))))
    else:
        raise SyntaxError("expected defun, defmacro, or defconstant")


def compile_mod_stage_1(args):
    """
    stage 1: collect up names of globals (functions, constants, macros)
    """

    functions = {}
    constants = {}
    macros = []
    main_local_arguments = ir_first(args)

    namespace = set()
    while True:
        args = ir_rest(args)
        if ir_nullp(ir_rest(args)):
            break
        parse_mod_sexp(ir_first(args), namespace, functions, constants, macros)

    uncompiled_main = ir_first(args)

    functions[MAIN_NAME] = ir_list(main_local_arguments, uncompiled_main)

    return functions, constants, macros


def do_compile_lambda(args):
    raise EvalError("unsupported", args)


def recurse_used_symbols(name, symbols_for_name, acc=[]):
    """create list of all symbols used by name (with transitive closure, counting repeats up to 2)"""
    for symbol in symbols_for_name[name]:
        acc = [symbol] + acc
        if symbol not in acc[1:]:
            acc = recurse_used_symbols(symbol, symbols_for_name, acc)
    return acc


def do_mod_context_for_mod(args):
    """
    args = (parms, code)
    returns:
        "functions_required" list of (name, parms_code, need-mod-context, in-mod-context) tuples
    """
    (functions, constants, macros) = compile_mod_stage_1(args.first())
    # for now, ignore constants and macros

    # build nonlocal_symbols_for_function_name
    nonlocal_symbols_for_function_name = {}
    for name, parms_code in functions.items():
        parms = ir_first(parms_code)
        code = ir_first(ir_rest(parms_code))

        local_symbol_table = set(ir_flatten(parms))

        def atom_filter(ir):
            if ir_type(ir) != Type.SYMBOL:
                return False
            if ir_as_atom(ir) in BUILT_INS:
                return False
            if ir_as_atom(ir) in local_symbol_table:
                return False
            return True

        nonlocal_symbols_for_function_name[name] = ir_flatten(code, filter=atom_filter)

    # now let's build up functions_required

    # create list of all symbols used by MAIN_NAME (with transitive closure, counting repeats up to 2)
    all_symbols = recurse_used_symbols(MAIN_NAME, nonlocal_symbols_for_function_name)

    counter = collections.Counter(all_symbols)

    symbols_used_multiple = [k for k, v in counter.items() if v > 1]
    symbols_used_once = [_ for _ in all_symbols if counter[_] == 1]

    need_mod_context = len(symbols_used_multiple) > 0
    in_mod_context = 0
    main_tuple = [MAIN_NAME, functions[MAIN_NAME], need_mod_context, in_mod_context]

    functions_required = [main_tuple]

    for name, parms_code in functions.items():
        if name not in all_symbols:
            continue
        child_symbols = recurse_used_symbols(name, nonlocal_symbols_for_function_name)
        need_mod_context = any(_ in symbols_used_multiple for _ in child_symbols)
        in_mod_context = name in symbols_used_multiple
        tuple = [name, parms_code, need_mod_context, in_mod_context]
        functions_required.append(tuple)

    function_names_in_mod_context = [_[0] for _ in functions_required if _[-1]]

    # now convert to ir types
    fnimc = ir_list(*[ir_new(Type.SYMBOL, _) for _ in function_names_in_mod_context])

    ir = ir_null()
    for name, parms_code, need_mod_context, in_mod_context in functions_required:
        nmc = ir_new(Type.INT, 1 if need_mod_context else 0)
        imc = ir_new(Type.INT, 1 if in_mod_context else 0)
        ir_entry = ir_list(ir_new(Type.SYMBOL, name), parms_code, nmc, imc)
        ir = ir_cons(ir_entry, ir)

    return 1, args.to(ir)
