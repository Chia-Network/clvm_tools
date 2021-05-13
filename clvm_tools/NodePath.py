r"""
We treat an s-expression as a binary tree, where leaf nodes are atoms and pairs
are nodes with two children. We then number the paths as follows:

              1
             / \
            /   \
           /     \
          /       \
         /         \
        /           \
       2             3
      / \           / \
     /   \         /   \
    4      6      5     7
   / \    / \    / \   / \
  8   12 10  14 9  13 11  15

etc.

You're probably thinking "the first two rows make sense, but why do the numbers
do that weird thing after?" The reason has to do with making the implementation simple.
We want a simple loop which starts with the root node, then processes bits starting with
the least significant, moving either left or right (first or rest). So the LEAST significant
bit controls the first branch, then the next-least the second, and so on. That leads to this
ugly-numbered tree.
"""


def compose_paths(path_0, path_1):
    """
    The binary representation of a path is a 1 (which means "stop"), followed by the
    path as binary digits, where 0 is "left" and 1 is "right".

    Look at the diagram at the top for these examples.

    Example: 9 = 0b1001, so right, left, left
    Example: 10 = 0b1010, so left, right, left

    How it works: we write both numbers as binary. We ignore the terminal in path_0, since it's
    not the terminating condition anymore. We shift path_1 enough places to OR in the rest of path_0.

    Example: path_0 = 9 = 0b1001, path_1 = 10 = 0b1010.
    Shift path_1 three places (so there is room for 0b001) to 0b1010000.
    Then OR in 0b001 to yield 0b1010001 = 81, which is right, left, left, left, right, left.
    """
    mask = 1
    temp_path = path_0
    while temp_path > 1:
        path_1 <<= 1
        mask <<= 1
        temp_path >>= 1

    mask -= 1
    path = path_1 | (path_0 & mask)
    return path


class NodePath:
    """
    Use 1-based paths
    """

    def __init__(self, index=1):
        if index < 0:
            byte_count = (index.bit_length() + 7) >> 3
            blob = index.to_bytes(byte_count, byteorder="big", signed=True)
            index = int.from_bytes((b"\0" + blob), byteorder="big", signed=False)
        self._index = index

    def as_short_path(self):
        index = self._index
        byte_count = (index.bit_length() + 7) >> 3
        return index.to_bytes(byte_count, byteorder="big")

    as_path = as_short_path

    def __add__(self, other_node):
        return self.__class__(compose_paths(self._index, other_node._index))

    def first(self):
        return self.__class__(self._index * 2)

    def rest(self):
        return self.__class__(self._index * 2 + 1)

    def __str__(self):
        return "NodePath: %d" % self._index

    def __repr__(self):
        return "NodePath: %d" % self._index


TOP = NodePath()
LEFT = TOP.first()
RIGHT = TOP.rest()
