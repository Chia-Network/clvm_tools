from clvm import to_sexp_f


from clvm_tools import binutils


"""
"function" is used in front of a constant uncompiled
program to indicate we want this program literal to be
compiled and quoted, so it can be passed as an argument
to a compiled clvm program.

EG: (function (+ 20 @)) should return (+ (quote 20) 1) when run.
Thus (opt (com (quote (function (+ 20 @)))))
should return (quote (+ (quote 20) 1))

(function PROG) => (opt (com (quote PROG) (quote MACROS)))

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
    (quote ("defmacro"
       (c (quote "list")
          (c (f 1)
             (c (c (quote "mod")
                   (c (f (r 1))
                      (c (f (r (r 1)))
                         (quote ()))))
                (quote ()))))))
    """,
    """
    ;(defmacro list ARGS
    ;    ((c (mod args
    ;        (defun compile-list
    ;               (args)
    ;               (if args
    ;                   qq (c (unquote (f args))
    ;                         (unquote (compile-list (r args)))))
    ;                   ()))
    ;            (compile-list args)
    ;        )
    ;        ARGS
    ;    ))
    ;)
    (quote (list
        ((c (quote ((c (f 1) (c (f 1) (c (r 1) (quote ()))))))
            (c (quote ((c (i (f (r 1))
                         (quote (c (quote #c)
                               (c (f (f (r 1)))
                                  (c ((c (f 1)
                                         (c (f 1)
                                            (c (r (f (r 1)))
                                               (quote ())))))
                                     (quote ())))))
                         (quote (quote ()))) 1)))
               1)))))
    """,
    """
    (defmacro function (BODY)
        (qq (opt (com (quote (unquote BODY))
                 (qq (unquote (macros)))
                 (qq (unquote (symbols)))))))""",
    """
    (defmacro if (A B C)
        (qq ((c
            (i (unquote A)
               (function (unquote B))
               (function (unquote C)))
            @))))""",
]


DEFAULT_MACRO_LOOKUP = None


def build_default_macro_lookup(eval):
    run = binutils.assemble("((c (com (f 1) (r 1)) 1))")
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
