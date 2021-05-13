import hashlib
import json

from typing import Any, Callable, List

from clvm import SExp

from .sha256tree import sha256tree

OpCallable = Callable[[Any, "ValStackType"], int]

ValStackType = List[SExp]
OpStackType = List[OpCallable]


PRELUDE = '''<html>
<head>
  <link rel="stylesheet"
      href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"
      integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T"
      crossorigin="anonymous">
  <script
      src="https://code.jquery.com/jquery-3.3.1.slim.min.js"
      integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo"
      crossorigin="anonymous"></script>
  <script
      src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js"
      integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1"
      crossorigin="anonymous"></script>
  <script
      src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"
      integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM"
      crossorigin="anonymous"></script>
</head>
<body>
<div class="container">
'''


TRAILER = "</div></body></html>"


def dump_sexp(s, disassemble):
    return '<span id="%s">%s</span>' % (id(s), disassemble(s))


def dump_invocation(form, rewrit_form, env, result, disassemble):
    print('<hr><div class="invocation" id="%s">' % id(form))
    print('<span class="form"><a name="id_%s">%s</a></span>' % (
        id(form), dump_sexp(form, disassemble)))
    print('<ul>')
    if form != rewrit_form:
        print(
            '<li>Rewritten as:<span class="form">'
            '<a name="id_%s">%s</a></span></li>' % (
                id(rewrit_form), dump_sexp(rewrit_form, disassemble)))
    for _, e in enumerate(env):
        print('<li>x%d: <a href="#id_%s">%s</a></li>' % (
            _, id(e), dump_sexp(e, disassemble)))
    print('</ul>')
    print('<span class="form">%s</span>' % dump_sexp(result, disassemble))
    if form.listp() and len(form) > 1:
        print('<ul>')
        for _, arg in enumerate(form[1:]):
            print('<li>arg %d: <a href="#id_%s">%s</a></li>' % (
                _, id(arg), dump_sexp(arg, disassemble)))
        print('</ul>')
    print("</div>")


def trace_to_html(invocations, disassemble):
    invocations = reversed(invocations)

    print(PRELUDE)

    id_set = set()
    id_list = []

    for form, rewrit_form, env, rv in invocations:
        dump_invocation(form, rewrit_form, env, rv, disassemble)
        the_id = id(form)
        if the_id not in id_set:
            id_set.add(the_id)
            id_list.append(form)

    print('<hr>')
    for _ in id_list:
        print('<div><a href="#id_%s">%s</a></div>' % (id(_), disassemble(_)))
    print('<hr>')

    print(TRAILER)


def build_symbol_dump(constants_lookup, run_program, path):
    compiled_lookup = {}
    for k, v in constants_lookup.items():
        cost, v1 = run_program(v, v.null())
        compiled_lookup[sha256tree(v1).hex()] = bytes(k).decode()
    output = json.dumps(compiled_lookup)
    with open(path, "w") as f:
        f.write(output)


def text_trace(disassemble, form, symbol, env, result):
    if symbol:
        env = env.rest()
        symbol = disassemble(env.to(symbol.encode()).cons(env))
    else:
        symbol = "%s [%s]" % (disassemble(form), disassemble(env))
    print("%s => %s" % (symbol, result))
    print("")


def table_trace(disassemble, form, symbol, env, result):
    if form.listp():
        sexp = form.first()
        args = form.rest()
    else:
        sexp = form
        args = form.null()
    print("exp:", disassemble(sexp))
    print("arg:", disassemble(args))
    print("env:", disassemble(env))
    print("val:", result)
    print("bexp:", sexp.as_bin())
    print("barg:", args.as_bin())
    print("benv:", env.as_bin())
    print("--")


def display_trace(trace, disassemble, symbol_table, display_fun):
    for item in trace:
        form, env, rv = item
        if rv is None:
            rv = "(didn't finish)"
        else:
            rv = disassemble(rv)
        h = sha256tree(form).hex()
        symbol = symbol_table.get(h) if symbol_table else symbol_table
        display_fun(disassemble, form, symbol, env, rv)


def trace_to_text(trace, disassemble, symbol_table):
    display_trace(trace, disassemble, symbol_table, text_trace)


def trace_to_table(trace, disassemble, symbol_table):
    display_trace(trace, disassemble, symbol_table, table_trace)


def make_trace_pre_eval(log_entries, symbol_table=None):
    def pre_eval_f(sexp, args):
        sexp, args = [SExp.to(_) for _ in [sexp, args]]
        if symbol_table:
            h = sha256tree(sexp).hex()
            if h not in symbol_table:
                return None
        log_entry = [sexp, args, None]
        log_entries.append(log_entry)

        def callback_f(r):
            log_entry[-1] = SExp.to(r)

        return callback_f

    return pre_eval_f
