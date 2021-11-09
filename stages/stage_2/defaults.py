from clvm import to_sexp_f


from clvm_tools import binutils


"""
"function" is used in front of a constant uncompiled
program to indicate we want this program literal to be
compiled and quoted, so it can be passed as an argument
to a compiled clvm program.

EG: (function (+ 20 @)) should return (+ (q . 20) 1) when run.
Thus (opt (com (q . (function (+ 20 @)))))
should return (q . (+ (q . 20) 1))

(function PROG) => (opt (com (q . PROG) (q . MACROS)))

We have to use "opt" as (com PROG) might leave
some partial "com" operators in there and our
goals is to compile PROG as much as possible.
"""


DEFAULT_MACROS_SRC = [
    """
    ; we have to compile this externally, since it uses itself
    ;(defmacro defmacro (name params body)
    ;    (qq (list (unquote name) (mod (unquote params) (unquote body))))
    ;)
    (q . ("defmacro"
       (c (q . "list")
          (c (f 1)
             (c (c (q . "mod")
                   (c (f (r 1))
                      (c (f (r (r 1)))
                         (q . ()))))
                (q . ()))))))
    """,
    """
    ;(defmacro list ARGS
    ;    ((c (mod args
    ;        (defun compile-list
    ;               (args)
    ;               (if args
    ;                   (qq (c (unquote (f args))
    ;                         (unquote (compile-list (r args)))))
    ;                   ()))
    ;            (compile-list args)
    ;        )
    ;        ARGS
    ;    ))
    ;)
    (q "list"
        (a (q #a (q #a 2 (c 2 (c 3 (q))))
                 (c (q #a (i 5
                             (q #c (q . 4)
                                   (c 9 (c (a 2 (c 2 (c 13 (q))))
                                           (q)))
                             )
                             (q 1))
                           1)
                    1))
            1))
    """,
    """
    (defmacro function (BODY)
        (qq (opt (com (q . (unquote BODY))
                 (qq (unquote (macros)))
                 (qq (unquote (symbols)))))))""",
    """
    (defmacro if (A B C)
        (qq (a
            (i (unquote A)
               (function (unquote B))
               (function (unquote C)))
            @)))""",
    # / operator at the clvm layer is becoming deprecated and
    # will be implemented using divmod.
    """(defmacro / (A B) (qq (f (divmod (unquote A) (unquote B)))))""",
]


DEFAULT_MACRO_LOOKUP = None

def build_default_macro_lookup(eval):
    run = binutils.assemble("(a (com 2 3) 1)")
    global DEFAULT_MACRO_LOOKUP
    for macro_src in DEFAULT_MACROS_SRC:
        macro_sexp = binutils.assemble(macro_src)
        env = macro_sexp.to((macro_sexp, DEFAULT_MACRO_LOOKUP))
        cost, new_macro = eval(run, env)
        DEFAULT_MACRO_LOOKUP = new_macro.cons(
            DEFAULT_MACRO_LOOKUP)
    return DEFAULT_MACRO_LOOKUP


def default_macro_lookup(eval):
    global DEFAULT_MACRO_LOOKUP
    if DEFAULT_MACRO_LOOKUP is None:
        DEFAULT_MACRO_LOOKUP = to_sexp_f([])
        DEFAULT_MACRO_LOOKUP = build_default_macro_lookup(eval)
    return DEFAULT_MACRO_LOOKUP
