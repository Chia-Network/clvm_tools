from clvm import KEYWORD_TO_ATOM


QUOTE_KW = KEYWORD_TO_ATOM["q"]


DEFAULT_MACROS_DEFINITIONS = [
    # defmacro
    """
    (q (defmacro (list defmacro_op (list q (f (a)))
                                   (list q (f (r (a))))
                                   (list q (f (r (r (a))))))))""",

    # qq
    """
    (defmacro qq (ARG) (
       list e
            (list q (compile_qq_op ARG))
            (list a)))
    """,

    # if
    """
    (defmacro if (ARG IF_TRUE IF_FALSE)
        (qq (e (i (unquote ARG)
                  (q (unquote IF_TRUE))
                  (q (unquote IF_FALSE)))
               (a))
         )
    )
    """,

    # lambda
    """
    (defmacro lambda (ARGS BODY)
       (list lambda_op (list q ARGS) (list q BODY)))
    """,
]


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

        sexp = eval_f(eval_f, macro_code, sexp.rest())


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
