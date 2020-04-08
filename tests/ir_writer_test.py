from clvm import to_sexp_f

from ir import reader, writer


def do_test(sexp_text):
    ir_sexp = reader.read_ir(sexp_text)
    sexp_text_normalized = writer.write_ir(ir_sexp)
    ir_sexp_2 = reader.read_ir(sexp_text)
    sexp_text_normalized_2 = writer.write_ir(ir_sexp_2)
    assert sexp_text_normalized == sexp_text_normalized_2


def test_writer_1():
    do_test('100')

    do_test('0x0100')

    do_test('0x100')

    do_test('"100"')

    do_test('"the quick brown fox jumps over the lazy dogs"')

    do_test('(the quick brown fox jumps over the lazy dogs)')

    do_test('foo')

    do_test('(100 0x0100)')

    do_test('()')

    do_test('(q ())')

    do_test('(c (q 100) (c (q "foo") (q ())))')

    do_test('(c . foo)')

    do_test('(a b c de f g h i . j)')
