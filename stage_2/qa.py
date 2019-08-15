from clvm import KEYWORD_TO_ATOM


QUOTE_KW = KEYWORD_TO_ATOM["q"]


def qa_sexp(sexp):
    """
    Quote atoms
    """
    if sexp.nullp() or not sexp.listp():
        return sexp.to([QUOTE_KW, sexp])

    operator = sexp.first()
    if not operator.listp():
        as_atom = operator.as_atom()
        if as_atom == QUOTE_KW:
            return sexp

    return sexp


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
