import hashlib


def sha256tree(v):
    pair = v.pair
    if pair:
        left = sha256tree(pair[0])
        right = sha256tree(pair[1])
        s = b"\2" + left + right
    else:
        s = b"\1" + v.atom
    return hashlib.sha256(s).digest()
