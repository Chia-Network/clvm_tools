# read strings into Token

from typing import Iterator, Optional, Tuple

from clvm import to_sexp_f
from clvm.CLVMObject import CLVMObject

from .Type import Type
from .utils import ir_new, ir_cons

Token = Tuple[str, int]
Stream = Iterator[Token]


def consume_whitespace(s: str, offset: int) -> int:
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


def consume_until_whitespace(s: str, offset: int) -> Token:
    start = offset
    while offset < len(s) and not s[offset].isspace() and s[offset] != ")":
        offset += 1
    return s[start:offset], offset


def next_cons_token(stream: Stream) -> Token:
    for token, offset in stream:
        break
    else:
        raise SyntaxError("missing )")
    return token, offset


def tokenize_cons(token: str, offset: int, stream: Stream) -> CLVMObject:
    if token == ")":
        return ir_new(Type.NULL, 0, offset)

    initial_offset = offset

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
    else:
        rest_sexp = tokenize_cons(token, offset, stream)
    return ir_cons(first_sexp, rest_sexp, initial_offset)


def tokenize_int(token: str, offset: int) -> Optional[CLVMObject]:
    try:
        return ir_new(Type.INT, int(token), offset)
    except (ValueError, TypeError):
        pass
    return None


def tokenize_hex(token: str, offset: int) -> Optional[CLVMObject]:
    if token[:2].upper() == "0X":
        try:
            token = token[2:]
            if len(token) % 2 == 1:
                token = "0%s" % token
            return ir_new(Type.HEX, bytes.fromhex(token), offset)
        except Exception:
            raise SyntaxError("invalid hex at %s: 0x%s" % (offset, token))
    return None


def tokenize_quotes(token: str, offset: int):
    if len(token) < 2:
        return None
    c = token[:1]
    if c not in "'\"":
        return None

    if token[-1] != c:
        raise SyntaxError("unterminated string starting at %s: %s" % (offset, token))

    q_type = Type.SINGLE_QUOTE if c == "'" else Type.DOUBLE_QUOTE

    return ((q_type, offset), token[1:-1].encode("utf8"))


def tokenize_symbol(token: str, offset: int):
    return ((Type.SYMBOL, offset), token.encode("utf8"))


def tokenize_sexp(token: str, offset: int, stream: Stream):

    if token == "(":
        token, offset = next_cons_token(stream)
        return tokenize_cons(token, offset, stream)

    for f in [
        tokenize_int,
        tokenize_hex,
        tokenize_quotes,
        tokenize_symbol,
    ]:
        r = f(token, offset)
        if r is not None:
            return r


def token_stream(s: str) -> Stream:
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
                yield s[start:offset + 1], start
                offset += 1
                continue
            else:
                raise SyntaxError(
                    "unterminated string starting at %s: %s" % (start, s[start:])
                )
        token, end_offset = consume_until_whitespace(s, offset)
        yield token, offset
        offset = end_offset


def read_ir(s: str, to_sexp=to_sexp_f):
    stream = token_stream(s)

    for token, offset in stream:
        return to_sexp(tokenize_sexp(token, offset, stream))
    else:
        raise SyntaxError("unexpected end of stream")
