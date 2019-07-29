# read strings into Token

import binascii
import enum

from clvm import to_sexp_f


class Type(enum.IntEnum):
    CONS = 1
    INT = 2
    HEX = 3
    QUOTES = 4
    SYMBOL = 5


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


def tokenize_cons(s: str, offset):
    c = s[offset]
    if c != "(":
        return None

    offset = consume_whitespace(s, offset+1)

    r = []
    while offset < len(s):
        c = s[offset]

        if c == ")":
            return r, offset + 1

        t, offset = tokenize_sexp(s, offset)
        r.append(t)
        offset = consume_whitespace(s, offset)

    raise SyntaxError("missing )")


def tokenize_int(s: str, offset):
    token, offset = consume_until_whitespace(s, offset)
    try:
        v = int(token)
        return v, offset
    except (ValueError, TypeError):
        return None


def tokenize_hex(s: str, offset):
    token, offset = consume_until_whitespace(s, offset)
    if token[:2].upper() == "0X":
        try:
            token = token[2:]
            if len(token) % 2 == 1:
                token = "0%s" % token
            return binascii.unhexlify(token), offset
        except Exception:
            raise SyntaxError("invalid hex at %s: %s" % (offset, token))


def tokenize_quotes(s: str, offset):
    c = s[offset]
    if c not in "\'\"":
        return None

    start = offset
    initial_c = s[start]
    offset += 1
    while offset < len(s) and s[offset] != initial_c:
        offset += 1
    if offset < len(s):
        return to_sexp_f(s[start:offset+1].encode("utf8")), offset + 1

    raise SyntaxError("unterminated string starting at %d: %s" % (start, s[start:]))


def tokenize_symbol(s: str, offset):
    token, offset = consume_until_whitespace(s, offset)
    return token.encode("utf8"), offset


def tokenize_sexp(s: str, offset: int):
    offset = consume_whitespace(s, offset)

    for type, f in [
        (Type.CONS, tokenize_cons),
        (Type.INT, tokenize_int),
        (Type.HEX, tokenize_hex),
        (Type.QUOTES, tokenize_quotes),
        (Type.SYMBOL, tokenize_symbol),
    ]:
        r = f(s, offset)
        if r is not None:
            sexp, end_offset = r
            sexp = to_sexp_f([type, sexp])
            sexp._offset = offset
            return sexp, end_offset

    raise SyntaxError("unexpected %s at %d" % (s[offset], offset))


def read_tokens(s: str):
    return tokenize_sexp(s, 0)[0]
