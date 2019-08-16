from clvm import KEYWORD_TO_ATOM, to_sexp_f
from opacity.binutils import disassemble

from .lambda_ import compile_lambda, compile_defmacro
from .macros import default_macro_lookup
from .mod import compile_mod
from .optimize import optimize_sexp


CONS_KW = KEYWORD_TO_ATOM["c"]
QUOTE_KW = KEYWORD_TO_ATOM["q"]
EVAL_KW = KEYWORD_TO_ATOM["e"]
ARGS_KW = KEYWORD_TO_ATOM["a"]


PASS_THROUGH_OPERATORS = set(
    KEYWORD_TO_ATOM[_] for _ in
    "e a i c f r l x = sha256 + - * . wrap unwrap point_add pubkey_for_exp".split()
)

for _ in "com opt exp mac".split():
    PASS_THROUGH_OPERATORS.add(_.encode("utf8"))


def run(sexp, args=[ARGS_KW]):
    return to_sexp_f([
        EVAL_KW, [b"com", [QUOTE_KW, sexp], [b"mac"]], args])


def compile_list(args):
    if not args.listp() or args.nullp():
        return to_sexp_f([QUOTE_KW, args])

    return [
        CONS_KW,
        args.first(),
        [b"list"] + list(args.rest().as_iter())]


def compile_function(args):
    return to_sexp_f([b"com", [QUOTE_KW, args.first()], [b"mac"]])


def compile_qq(args):
    return compile_qq_sexp(args.first())


def compile_qq_sexp(sexp):
    if not sexp.listp() or sexp.nullp():
        return to_sexp_f([QUOTE_KW, sexp])

    if (sexp.listp() and not sexp.first().listp()
            and sexp.first().as_atom() == b"unquote"):
        return sexp.rest().first()

    return to_sexp_f([b"list"] + [[b"qq", _] for _ in sexp.as_iter()])


COMPILE_BINDINGS = {
    b"list": compile_list,
    b"function": compile_function,
    b"qq": compile_qq,
    b"lambda": compile_lambda,
    b"defmacro": compile_defmacro,
    b"mod": compile_mod,
}


def do_exp_sexp(sexp, macro_lookup):
    # quote atoms
    if sexp.nullp() or not sexp.listp():
        return sexp.to([QUOTE_KW, sexp])

    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return sexp

        if as_atom == b"mac":
            return sexp.to([QUOTE_KW, macro_lookup])

        for macro_pair in macro_lookup.as_iter():
            macro_name = macro_pair.first()
            if macro_name.as_atom() == as_atom:
                macro_code = macro_pair.rest().first()
                post_sexp = run(macro_code, [QUOTE_KW, sexp.rest()])
                return run(post_sexp)

        if as_atom in COMPILE_BINDINGS:
            f = COMPILE_BINDINGS[as_atom]
            post_sexp = f(sexp.rest())
            return run(post_sexp)
    return None


def do_com_sexp(sexp, macro_lookup):
    expanded_sexp = do_exp_sexp(sexp, macro_lookup)
    if expanded_sexp:
        return expanded_sexp

    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        remaining_args = to_sexp_f([
            run(_) for _ in sexp.rest().as_iter()])

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
        macro_lookup = default_macro_lookup()
    compiled_sexp = do_com_sexp(new_sexp, macro_lookup)
    optimized_sexp = optimize_sexp(compiled_sexp, eval_f)
    return optimized_sexp


def do_exp(sexp, eval_f):
    new_sexp = sexp.first()
    if not sexp.rest().nullp():
        macro_lookup = sexp.rest().first()
    else:
        macro_lookup = default_macro_lookup()
    expanded_sexp = do_exp_sexp(new_sexp, macro_lookup)
    if expanded_sexp:
        return expanded_sexp
    return new_sexp
