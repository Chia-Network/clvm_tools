import binascii

from clvm import to_sexp_f

from clvm.make_eval import EvalError

from opacity import binutils

from .expand import op_expand_op


from ir.Type import Type


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def static_eval(sexp):
    # TODO: improve, and do deep eval if possible
    operator = sexp.first()
    if not operator.listp():
        if not operator.nullp():
            as_atom = operator.as_atom()
            if as_atom == "quote":
                return sexp.rest().first()
    raise EvalError("non static value", sexp)


def ir_type(ir_sexp):
    return ir_sexp.first()


def ir_nullp(ir_sexp):
    return ir_type(ir_sexp) == Type.CONS and ir_sexp.rest().nullp()


def ir_as_sexp(ir_sexp):
    if ir_nullp(ir_sexp):
        return to_sexp_f([])
    if ir_type(ir_sexp) == Type.CONS:
        return ir_as_sexp(ir_first(ir_sexp)).cons(ir_as_sexp(ir_rest(ir_sexp)))
    return ir_sexp.rest()


def ir_is_atom(ir_sexp):
    return ir_type(ir_sexp) != Type.CONS


def ir_first(ir_sexp):
    return ir_sexp.rest().first()


def ir_rest(ir_sexp):
    return ir_sexp.rest().rest()


def ir_symbol(ir_sexp):
    if ir_type(ir_sexp) == Type.SYMBOL:
        return ir_as_sexp(ir_sexp).as_atom().decode("utf8")


def ir_iter(ir_sexp):
    while True:
        if ir_type(ir_sexp) == Type.CONS:
            if ir_nullp(ir_sexp):
                break
            yield ir_first(ir_sexp)
            ir_sexp = ir_rest(ir_sexp)


def check_arg_count(args, count):
    if len(args.as_python()) != count:
        raise SyntaxError("bad argument count %d instead of %d" % (actual_count, count))


def compile_test_operator(args):
    return binutils.assemble("(30 (+ (q 100) (q 10)))")


def make_compile_remap(compiled_keyword):
    def do_compile(args):
        return binutils.assemble(compiled_keyword).cons(args)
    return do_compile


def quote_arg(arg):
    return to_sexp_f([binutils.assemble("q"), arg])


def compile_if_operator(args):
    # TODO: make this a macro
    # (if A B C) => (e (i A (q B) (q C)) (a))
    check_arg_count(args, 3)
    b = args.rest().first()
    c = args.rest().rest().first()
    abc = to_sexp_f([args.first(), quote_arg(b), quote_arg(c)])
    r = binutils.assemble("e").cons(
        binutils.assemble("i").cons(abc).cons(binutils.assemble("((a))")))
    return r


def compile_function_op(args):
    return binutils.assemble("q").cons(args)


COMPILE_OPERATOR_LOOKUP = dict(
    test=compile_test_operator,
)


COMPILE_OPERATOR_LOOKUP.update({
    "if": compile_if_operator,
    "function_op": compile_function_op,
})


def make_simple_replacement(src_opcode, obj_opcode=None):
    if obj_opcode is None:
        obj_opcode = src_opcode
    return [src_opcode.encode("utf8"), binutils.assemble("(c (q #%s) (a))" % obj_opcode)]
    


DEFAULT_REWRITE_RULES = to_sexp_f([
    make_simple_replacement("+"),
    make_simple_replacement("-"),
    make_simple_replacement("*"),
    make_simple_replacement("cons", "c"),
    make_simple_replacement("first", "f"),
    make_simple_replacement("rest", "r"),
    make_simple_replacement("args", "a"),
    make_simple_replacement("equal", "="),
    make_simple_replacement("="),
    make_simple_replacement("sha256"),
    make_simple_replacement("wrap"),
    [b"test", binutils.assemble("(q (30 (+ (q 100) (q 10))))")],
])


def op_compile_op(args, eval_f):
    if len(args.as_python()) not in (1, 2):
        raise SyntaxError("compile_op needs 1 or 2 arguments")

    ir_sexp = args.first()
    if args.rest().nullp():
        rewrite_rules = DEFAULT_REWRITE_RULES
    else:
        rewrite_rules = args.rest().first()

    if ir_nullp(ir_sexp):
        return binutils.assemble("(q ())")

    if ir_is_atom(ir_sexp):
        return to_sexp_f([binutils.assemble("#q"), ir_as_sexp(ir_sexp)])

    operator = ir_symbol(ir_first(ir_sexp))

    # handle "quote" special
    if operator == "quote":
        sexp = ir_as_sexp(ir_sexp)
        return binutils.assemble("#q").cons(sexp.rest())

    compiled_args = []
    for _ in ir_iter(ir_rest(ir_sexp)):
        r = op_compile_op(to_sexp_f([_]), eval_f)
        compiled_args.append(r)

    for pair in rewrite_rules.as_iter():
        if operator == pair.first().as_atom().decode("utf8"):
            code = pair.rest().first()
            r = eval_f(eval_f, code, compiled_args)
            return r

    raise ValueError("can't compile %s" % operator)


"""
Copyright 2019 Chia Network Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
