from clvm import KEYWORD_TO_ATOM, to_sexp_f
from opacity.binutils import disassemble

from .lambda_ import compile_lambda, compile_defmacro
from .mod import compile_mod


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]


PASS_THROUGH_OPERATORS = set(
    KEYWORD_TO_ATOM[_] for _ in
    "e a i c f r l x = sha256 + - * . wrap unwrap point_add pubkey_for_exp".split()
)

for _ in "com substitute_functions".split():
    PASS_THROUGH_OPERATORS.add(_.encode("utf8"))


def compile_list(args):
    if not args.listp() or args.nullp():
        return to_sexp_f([QUOTE_KW, args])

    return to_sexp_f([
        CONS_KW,
        args.first(),
        compile_list(args.rest())])


def compile_function(args):
    return to_sexp_f([b"com", [QUOTE_KW, args.first()]])


COMPILE_BINDINGS = {
    b"list": compile_list,
    b"function": compile_function,
    b"lambda": compile_lambda,
    b"defmacro": compile_defmacro,
    b"mod": compile_mod,
}


def optimize(r, eval_f):
    r1 = eval_f(eval_f, r, r.null())
    return to_sexp_f([QUOTE_KW, r1])


def do_compile_sexp(eval_f, sexp, macro_lookup):
    # quote atoms
    if sexp.nullp() or not sexp.listp():
        return to_sexp_f([QUOTE_KW, sexp])

    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return sexp

        for macro_pair in macro_lookup.as_iter():
            macro_name = macro_pair.first()
            if macro_name.as_atom() == as_atom:
                breakpoint()
                macro_code = macro_pair.rest().first()
                post_sexp = eval_f(eval_f, macro_code, sexp.rest())
                return do_compile_sexp(eval_f, post_sexp, macro_lookup)

        if as_atom in COMPILE_BINDINGS:
            f = COMPILE_BINDINGS[as_atom]
            post_sexp = f(sexp.rest())
            r = do_compile_sexp(eval_f, post_sexp, macro_lookup)
            # OPTIMIZE
            r = optimize(r, eval_f)
            return r

        remaining_args = to_sexp_f([
            do_compile_sexp(
                eval_f, _, macro_lookup) for _ in sexp.rest().as_iter()])

        if as_atom == b"com":
            if remaining_args.first().first().as_atom() == QUOTE_KW:
                const_sexp = remaining_args.first().rest().first()
                compiled_sexp = do_compile_sexp(eval_f, const_sexp, macro_lookup)
                return to_sexp_f([QUOTE_KW, compiled_sexp])
            return to_sexp_f(as_atom).cons(remaining_args)

        if as_atom in PASS_THROUGH_OPERATORS:
            return to_sexp_f(as_atom).cons(remaining_args)

    raise SyntaxError(
        "can't compile %s, unknown operator" %
        disassemble(sexp))


def do_com(sexp, eval_f):
    new_sexp = sexp.first()
    if not sexp.rest().nullp():
        macro_lookup = sexp.rest().first()
    else:
        macro_lookup = sexp.null()
    return do_compile_sexp(eval_f, new_sexp, macro_lookup)