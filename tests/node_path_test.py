from clvm.casts import int_from_bytes

from clvm_tools.NodePath import NodePath, TOP, LEFT, RIGHT

LEFT_RIGHT_LEFT = LEFT + RIGHT + LEFT


def reset(n):
    path_blob = n.as_short_path()
    index = int_from_bytes(path_blob)
    n = NodePath(index)
    return n


def cmp_to_bits(n, bits):
    n_as_int = int(f"0x{n.as_short_path().hex()}", 16)
    bits_as_int = int(f"0b{bits}", 2)
    assert n_as_int == bits_as_int


def test_node_path():
    n = TOP
    assert n.as_short_path().hex() == "01"
    n = reset(n)
    n += LEFT
    assert n.as_short_path().hex() == "02"
    n = reset(n)
    n += RIGHT
    assert n.as_short_path().hex() == "06"
    n = reset(n)
    n += RIGHT
    assert n.as_short_path().hex() == "0e"
    n = reset(n)
    n += LEFT
    assert n.as_short_path().hex() == "16"
    n = reset(n)
    n += LEFT
    assert n.as_short_path().hex() == "26"
    n = reset(n)
    n += LEFT
    assert n.as_short_path().hex() == "46"
    n = reset(n)
    n += RIGHT
    assert n.as_short_path().hex() == "c6"
    n = reset(n)
    n += LEFT
    cmp_to_bits(n, "101000110")
    n = reset(n)
    n += LEFT_RIGHT_LEFT
    cmp_to_bits(n, "101001000110")
    n = reset(n)
    n += LEFT_RIGHT_LEFT
    cmp_to_bits(n, "101001001000110")
    n = reset(n)
    n += LEFT_RIGHT_LEFT
    cmp_to_bits(n, "101001001001000110")
    n = reset(n)
    cmp_to_bits(n, "101001001001000110")


def test_revive_index():
    for idx in range(2048):
        n = NodePath(idx)
        n1 = reset(n)
        assert n.as_short_path() == n1.as_short_path()
