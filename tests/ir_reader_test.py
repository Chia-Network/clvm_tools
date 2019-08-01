
from ir import reader


def test_reader_1():
    sexp = reader.read_ir('(100 0x0100)')
    print(sexp)

    sexp = reader.read_ir('100')
    print(sexp)

    sexp = reader.read_ir('0x0100')
    print(sexp)

    sexp = reader.read_ir('0x100')
    print(sexp)

    sexp = reader.read_ir('"100"')
    print(sexp)

    sexp = reader.read_ir('foo')
    print(sexp)

    sexp = reader.read_ir('(c (q 100) (c (q "foo") (q ())))')
    print(sexp)

    sexp = reader.read_ir('(c . foo)')
    print(sexp)
