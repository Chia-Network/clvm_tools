This is the in-development version of clvm_tools for clvm, which implements, a LISP-like language for encumbering and releasing funds with smart-contract capabilities.


Set up your virtual environments:

    $ python3 -m venv env
    $ ln -s env/bin/activate
    $ . ./activate
    $ pip install -r requirements.txt
    $ pip install -e .

Optionally, run unit tests for a sanity check.

    $ pip install pytest
    $ py.test tests


The language has two components: the higher level language and the compiled lower level language which runs on the clvm.
To compile the higher level language into the lower level language use:

    $ run -s2 '(mod ARGUMENT (+ ARGUMENT 3))'
    (+ (a) (q 3))

To execute this code:

    $ brun '(+ (a) (q 3))' '2'
    5
