from clvm import to_sexp_f
from clvm import KEYWORD_TO_ATOM

from opacity import binutils

from .qq import compile_qq_sexp


QUOTE_KW = KEYWORD_TO_ATOM["q"]


IF_MACRO = binutils.disassemble(compile_qq_sexp(binutils.assemble(
    '(e (i (unquote (f (a))) (q (unquote (f (r (a))))) '
    '(q (unquote (f (r (r (a))))))) (a))')))


DEFAULT_MACROS = [
    ("bool",
        "(list #i (f (a)) 1 ())"),
    ("not",
        "(list #i (f (a)) () 1)"),
    ("if", IF_MACRO),
    ("qq",
        "(list #q (compile_qq_op (list #q (f (a)))))"),
]


DEFAULT_MACRO_LOOKUP = to_sexp_f([
    [op.encode("utf8"), binutils.assemble(code)]
    for op, code in DEFAULT_MACROS
])


def expand_sexp(sexp, macro_lookup, eval_f):
    """
    Expand macros
    """
    while True:
        if sexp.nullp() or not sexp.listp():
            return sexp

        operator = sexp.first()
        if operator.listp():
            return sexp

        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return sexp

        for macro_pair in macro_lookup.as_iter():
            macro_name = macro_pair.first()
            if macro_name.as_atom() == as_atom:
                break
        else:
            return sexp

        macro_code = macro_pair.rest().first()

        expanded_sexp = eval_f(eval_f, macro_code, sexp.rest())
        sexp = eval_f(eval_f, expanded_sexp, sexp.null())


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
