from clvm import KEYWORD_TO_ATOM

from .lambda_ import compile_lambda


# (lambda x (* x x)) => (quote (* (a) (a)))
# lambda_op
# (symbol_replace sexp symbol_table)
# (symbol_table sexp) => symbol_table

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


def build_invocation(imp, args):
    from .compile import compile_list
    new_args = compile_list(args)
    sexp = args.to([EVAL_KW, [QUOTE_KW, imp], new_args])
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


def compile_mod(args):
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
        imp = compile_lambda(declaration_sexp)
        definitions[function_name.as_atom()] = imp

    main_lambda = args.to([main_symbols, args.first()])
    main_sexp = compile_lambda(main_lambda)

    definition_table = [b"list"] + [
        [b"list"] + list(_) for _ in definitions.items()]
    return args.to([b"substitute_functions", main_sexp, definition_table])


def do_substitute_functions(args, eval_f):
    main_sexp = args.first()
    definitions_list = args.rest().first()
    definitions = {}
    for pair in definitions_list.as_iter():
        definitions[pair.first().as_atom()] = pair.rest().first()
    breakpoint()
    return substitute_functions(main_sexp, definitions)
