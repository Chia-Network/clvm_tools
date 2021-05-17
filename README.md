# Introduction

This is the in-development version of `clvm_tools` for clvm, which implements, a LISP-like language for encumbering and releasing funds with smart-contract capabilities.


# Set up

Set up your virtual environments

    $ python3 -m venv venv
    $ . ./venv/bin/activate (windows: venv\Scripts\activate.bat)
    $ pip install -e .

If you run into any issues, be sure to check out [this section of the wiki](https://github.com/Chia-Network/chia-blockchain/wiki/Help-with-clvm_tools)

Optionally, run unit tests for a sanity check.

    $ pip install pytest
    $ py.test tests


# Quick examples

The language has two components: the higher level language and the compiled lower level language which runs on the clvm.
To compile the higher level language into the lower level language use:

    $ run '(mod ARGUMENT (+ ARGUMENT 3))'
    (+ 1 (q . 3))

To execute this code:

    $ brun '(+ 1 (q . 3))' '2'
    5


# The Compiler


## Basic example

The high level language is a superset of [clvm](https://github.com/Chia-Network/clvm), adding several operators. The main supported operator is `mod` which lets you define a set of macros and functions, and an entry point that calls them. Here's an example.

    (mod (INDEX)
         (defun factorial (VALUE) (if (= VALUE 1) 1 (* VALUE (factorial (- VALUE 1)))))
         (factorial INDEX)
         )

You can copy this to a file `fact.clvm`, then compile it with `run fact.clvm` and you'll see output like

`(a (q 2 2 (c 2 (c 5 ()))) (c (q 2 (i (= 5 (q . 1)) (q 1 . 1) (q 18 5 (a 2 (c 2 (c (- 5 (q . 1)) ()))))) 1) 1))`

You can then run this code with `brun`, passing in a parameter. Or pipe it using this `bash` quoting trick:

    $ brun "`run fact.clvm`" "(5)"
    120

This affirms that 5! = 120.


### Auto-quoting of literals

Note that the `1` is not quoted. The compiler recognizes and auto-quotes constant values.

    $ run 15
    15
    $ brun 15
    FAIL: not a list 15

## Known operators

Besides `mod` and `defun`, the compiler has a few more built-in operators:

### @

Instead of evaluating `1` to return the arguments, you should use `@` in the higher level language.
This is easier for humans to read, and calling `(f @)` will be compiled to 2, etc.

```
    $ run '@' '("example" 200)'
    ("example" 200)
    
    $ run '(mod ARGS (f (r @)))'
    5
```

You generally won't need to use `@`; it's better to use `mod` and named arguments.


### (if)

`(if A B C)`
This operator is similar to lone condition in clvm `i`, except it actually does a lazy evaluation of either B or C (depending upon A). This allows you to put expensive or failing (like `x`) operator within branches, knowing they won't be executed unless required.

This is implemented as a macro, and expands out to `((c (i A (q B) (q C)) (a)))`.


### (qq) and (unquote)

`(qq EXPR)` for expanding templates. This is generally for creating your own operators that end up being inline functions.

Everything in `EXPR` is quoted literally, unless it's wrapped by a unary `unquote` operator, in which case, it's evaluated. So

`(qq (+ 5 (a)))` would expand to `(+ 5 (a))`

But `(qq (+ 5 (unquote (+ 9 10))))` would expand to `(+ 5 19)` because `(+ 9 10)` is `19`.

And `(qq (+ 5 (unquote (+ 1 (a)))))` expands to something that depends on what `(a)` is in the context it's evaluated. (It'd better be a number so 1 can be added to it!)

If you have a template expression and you want to substitute values into it, this is what you use.


## Macros

You can also define macros within a module, which act as inline functions. When a previously defined macro operator is encountered, it "rewrites" the existing statement using the macro, passing along the arguments as literals (ie. they are not evaluated).


### A Simple Example

    (mod (VALUE1 VALUE2)
         (defmacro sum (A B) (qq (+ (unquote A) (unquote B))))
         (sum VALUE1 VALUE2)
         )

When `run`, this produces the following output:

`(+ 2 5)`

Compare to the function version:

    (mod (VALUE1 VALUE2)
         (defun sum (A B) (+ A B))
         (sum VALUE1 VALUE2)
         )

which produces

`(a (q 2 2 (c 2 (c 5 (c 11 ())))) (c (q 16 5 11) 1))`

There's a lot more going on here, setting up an environment where sum would be allowed to call itself recursively.

### Inline functions

If you want to write a function that is always inlined, use `defun-inline`.


    (mod (VALUE1 VALUE2)
         (defun-inline sum (A B) (+ A B))
         (sum VALUE1 VALUE2)
         )

This produces the much more compact output `(+ 2 5)`.

Inline functions *must not* be recursive.


### A More Complex Example

Here's an example, demonstrating how `if` is defined.

    (mod (VALUE1 VALUE2)
         (defmacro my_if (A B C)
           (qq ((c
    	    (i (unquote A)
    	       (function (unquote B))
    	       (function (unquote C)))
    	    (a)))))
         (my_if (= (+ VALUE1 VALUE2) 10) "the sum is 10" "the sum is not 10")
         )

This produces

`((c (i (= (+ 2 5) (q 10)) (q (q "the sum is 10")) (q (q "the sum is not 10"))) 1))`

which is not much code, for how much source there is. This also demonstrates the general notion that macros (and inline functions) cause much less code bloat than functions. The main disadvantages is that macros are not recursive (since they run at compile time) and they're messier to write.
