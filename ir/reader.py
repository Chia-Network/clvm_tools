# read strings into Token

from clvm import to_sexp_f


from .Type import Type


def consume_whitespace(s: str, offset):
    """
    This also deals with comments.
    """
    while True:
        while offset < len(s) and s[offset].isspace():
            offset += 1
        if offset >= len(s) or s[offset] != ";":
            break
        while offset < len(s) and s[offset] not in "\n\r":
            offset += 1
    return offset


def consume_until_whitespace(s: str, offset):
    start = offset
    while offset < len(s) and not s[offset].isspace() and s[offset] != ")":
        offset += 1
    return s[start:offset], offset


def next_cons_token(stream):
    for token, offset in stream:
        break
    else:
        raise SyntaxError("missing )")
    return token, offset


def tokenize_cons(token, offset, stream):
    if token == ")":
        return []

    first_sexp = tokenize_sexp(token, offset, stream)

    token, offset = next_cons_token(stream)
    if token == ".":
        dot_offset = offset
        # grab the last item
        token, offset = next_cons_token(stream)
        rest_sexp = tokenize_sexp(token, offset, stream)
        token, offset = next_cons_token(stream)
        if token != ")":
            raise SyntaxError("illegal dot expression at %s" % dot_offset)
        return first_sexp.cons(rest_sexp)

    rest_sexp = tokenize_list_items(token, offset, stream)
    return first_sexp.cons(rest_sexp)


def tokenize_int(token, offset):
    try:
        return int(token)
    except (ValueError, TypeError):
        return None


def tokenize_hex(token, offset):
    if token[:2].upper() == "0X":
        try:
            token = token[2:]
            if len(token) % 2 == 1:
                token = "0%s" % token
            return bytes.fromhex(token)
        except Exception:
            raise SyntaxError("invalid hex at %s: 0x%s" % (offset, token))


def tokenize_quotes(token, offset):
    if len(token) < 2:
        return None
    c = token[:1]
    if c not in "\'\"":
        return None

    if token[-1] != c:
        raise SyntaxError(
            "unterminated string starting at %s: %s" % (offset, token))

    return token[1:-1].encode("utf8")


def tokenize_symbol(token, offset):
    return token.encode("utf8")


def tokenize_list_items(token, offset, stream):
    r = tokenize_cons(token, offset, stream)
    sexp = to_sexp_f((Type.CONS, r))
    sexp._offset = offset
    return sexp


def tokenize_sexp(token, offset, stream):

    if token == "(":
        token, offset = next_cons_token(stream)
        return tokenize_list_items(token, offset, stream)

    for type, f in [
        (Type.INT, tokenize_int),
        (Type.HEX, tokenize_hex),
        (Type.QUOTES, tokenize_quotes),
        (Type.SYMBOL, tokenize_symbol),
    ]:
        r = f(token, offset)
        if r is not None:
            sexp = to_sexp_f((type, r))
            sexp._offset = offset
            return sexp


def token_stream(s: str):
    offset = 0
    while offset < len(s):
        offset = consume_whitespace(s, offset)
        if offset >= len(s):
            break
        c = s[offset]
        if c in "(.)":
            yield c, offset
            offset += 1
            continue
        if c in "\"'":
            start = offset
            initial_c = s[start]
            offset += 1
            while offset < len(s) and s[offset] != initial_c:
                offset += 1
            if offset < len(s):
                yield s[start:offset+1], initial_c
                offset += 1
                continue
            else:
                raise SyntaxError(
                    "unterminated string starting at %s: %s" % (
                        start, s[start:]))
        token, end_offset = consume_until_whitespace(s, offset)
        yield token, offset
        offset = end_offset


def read_ir(s: str):
    stream = token_stream(s)

    for token, offset in stream:
        return tokenize_sexp(token, offset, stream)
    else:
        raise SyntaxError("unexpected end of stream")
