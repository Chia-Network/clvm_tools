from clvm import KEYWORD_TO_ATOM

from .lambda_ import do_lambda_op


# (lambda x (* x x)) => (quote (* (a) (a)))
# lambda_op
# (symbol_replace sexp symbol_table)
# (symbol_table sexp) => symbol_table

ARGS_KW = KEYWORD_TO_ATOM["a"]
FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
CONS_KW = KEYWORD_TO_ATOM["c"]
EVAL_KW = KEYWORD_TO_ATOM["e"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


"""
(mod (N)
    (defun fact K (if (= K 1) 1 (* K (fact (- K 1)))))
    (defun next_fib (n0 n1) (list n1 (+ n0 n1)))
    (defun fib2 N (if (= N 0) (q (0 1)) (next_fib (fib2 (- N 1)))))
    (defun fib N (first (fib2 N)))
    (+ (fib N) (fact N))
)
"""


"""
(mod (A B)
    (defun square (N) (* N N))
    (defun hyp (A B) (+ (square A) (square B)))
    (hyp A B)
)
"""


def op_compile_list(args):
    if not args.listp() or args.nullp():
        return args.to([QUOTE_KW, args])

    return args.to([
        CONS_KW,
        args.first(),
        op_compile_list(args.rest())])


def build_invocation(imp, args):
    new_args = op_compile_list(args)
    sexp = imp.to([EVAL_KW, [QUOTE_KW, imp], new_args])
    return sexp


def substitute_functions(sexp, definitions):
    if sexp.nullp() or not sexp.listp():
        return sexp

    operator = sexp.first()
    if operator.listp():
        return sexp

    args = sexp.to([substitute_functions(
        _, definitions) for _ in sexp.rest().as_iter()])
    op = operator.as_atom()
    for f_name, imp in definitions.items():
        if f_name == op:
            break
    else:
        return sexp.to([operator] + list(args.as_iter()))

    # substitute!
    new_imp = substitute_functions(imp, definitions)
    return build_invocation(new_imp, args)


def do_mod_op(args, eval_f):
    definitions = {}
    main_symbols = args.first()
    while True:
        args = args.rest()
        if args.rest().nullp():
            break
        declaration_sexp = args.first()
        if declaration_sexp.first().as_atom() != b"defun":
            raise SyntaxError("expected defun")
        declaration_sexp = declaration_sexp.rest()
        function_name = declaration_sexp.first()
        declaration_sexp = declaration_sexp.rest()
        imp = do_lambda_op(declaration_sexp, eval_f)
        definitions[function_name.as_atom()] = imp

    main_lambda = args.to([main_symbols, args.first()])
    main_sexp = do_lambda_op(main_lambda, eval_f)

    return substitute_functions(main_sexp, definitions)
