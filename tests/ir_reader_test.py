from clvm import to_sexp_f

from ir import reader


def test_reader_1():
    sexp = reader.read_ir('100', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('(100 0x0100)', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('0x0100', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('0x100', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('"100"', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir("'100'", to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('foo', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('(c (q 100) (c (q "foo") (q ())))', to_sexp_f)
    print(sexp)

    sexp = reader.read_ir('(c . foo)', to_sexp_f)
    print(sexp)
