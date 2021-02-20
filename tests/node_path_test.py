from clvm.casts import int_from_bytes, int_to_bytes

from clvm_tools.NodePath import NodePath, TOP, LEFT, RIGHT


def reset(n):
    path_blob = n.as_short_path()
    index = int_from_bytes(path_blob)
    n = NodePath(index)
    return n


def test_node_path():
    left_right_left = TOP + LEFT + RIGHT + LEFT
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
    assert n.as_short_path().hex() == "0146"


def test_revive_index():
    for idx in range(2048):
        n = NodePath(idx)
        n1 = reset(n)
        assert n.as_short_path() == n1.as_short_path()
