
from ir import reader


def test_reader_1():
    sexp = reader.read_tokens('(100 0x0100)')
    print(sexp)

    sexp = reader.read_tokens('100')
    print(sexp)

    sexp = reader.read_tokens('0x0100')
    print(sexp)

    sexp = reader.read_tokens('0x100')
    print(sexp)

    sexp = reader.read_tokens('"100"')
    print(sexp)

    sexp = reader.read_tokens('foo')
    print(sexp)

    sexp = reader.read_tokens('(c (q 100) (c (q "foo") (q ())))')
    print(sexp)

    sexp = reader.read_tokens('(c . foo)')
    print(sexp)
