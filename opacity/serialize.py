
def encode_size(f, size, step_size, base_byte_int):
    step_count, remainder = divmod(size, step_size)
    if step_count > 0:
        f.write(b'\x60')
        step_count -= 1
        while step_count > 0:
            step_count, r = divmod(step_count, 32)
            f.write(bytes([r]))
    f.write(bytes([base_byte_int+remainder]))


def list_size(v):
    """
    Calculate list size
    """
    if v.nullp():
        return 0

    if v.listp():
        t = list_size(v.rest())
        if t is not None:
            return t + 1
    return t


def sexp_to_stream(v, f):
    if v.listp():
        size = list_size(v)
        encode_size(f, size, 32, 0x20)
        for _ in range(size):
            sexp_to_stream(v.first(), f)
            v = v.rest()
        return

    as_atom = v.as_atom()
    if isinstance(as_atom, bytes):
        blob = as_atom
        size = len(blob)
        if size == 0:
            f.write(b'\0')
            return
        if size == 1:
            v1 = v.as_int()
            if v1 and 0 < v1 <= 31:
                f.write(bytes([v1 & 0x3f]))
                return
        encode_size(f, size, 160, 0x60)
        f.write(blob)
        return

    assert 0


def decode_size(f):
    steps = 0
    b = f.read(1)
    if len(b) == 0:
        raise ValueError("unexpected end of stream")
    v = b[0]
    if v == 0x60:
        steps = 1
        shift_count = 0
        while True:
            b = f.read(1)
            if len(b) == 0:
                raise ValueError("unexpected end of stream")
            v = b[0]
            if v >= 0x20:
                break
            steps += (v << shift_count)
            shift_count += 5

    return steps, v


def sexp_from_stream(f, to_sexp):
    steps, v = decode_size(f)
    if v == 0:
        return to_sexp(b'')

    if v < 0x20:
        return to_sexp(bytes([v]))

    if v < 0x40:
        size = v - 0x20 + steps * 0x20
        items = [sexp_from_stream(f, to_sexp) for _ in range(size)]
        return to_sexp(items)

    size = v - 0x60 + steps * 160
    blob = f.read(size)
    if len(blob) < size:
        raise ValueError("unexpected end of stream")
    return to_sexp(blob)
