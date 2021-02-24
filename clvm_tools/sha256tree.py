import hashlib


def sha256tree(v):
    pair = v.as_pair()
    if pair:
        left = sha256tree(pair[0])
        right = sha256tree(pair[1])
        s = b"\2" + left + right
    else:
        atom = v.as_atom()
        s = b"\1" + atom
    return hashlib.sha256(s).digest()
