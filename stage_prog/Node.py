from clvm import KEYWORD_TO_ATOM, to_sexp_f


FIRST_KW = KEYWORD_TO_ATOM["f"]
REST_KW = KEYWORD_TO_ATOM["r"]
ARGS_KW = KEYWORD_TO_ATOM["a"]


class Node:
    def __init__(self, index=0):
        self._index = index

    @classmethod
    def for_list_index(class_, index):
        return Node().list_index(index)

    def list_index(self, index):
        node = self
        while index > 0:
            node = node.rest()
            index -= 1
        return node.first()

    def path_iter(self):
        """
        Yields 0s and 1s where 1 means "first" and 0 means "rest"
        """

        def iter(n):
            if n == 0:
                return
            yield from iter((n-1) >> 1)
            yield n & 1

        return iter(self._index)

    @classmethod
    def path_for_iter(class_, iter, base=None):
        base = base or [ARGS_KW]
        for direction in iter:
            if direction:
                base = [FIRST_KW, base]
            else:
                base = [REST_KW, base]
        return base

    def path(self, base=None):
        """
        Generate code that drills down to correct args node.
        n: a path, where 0 means "here", 1 means "first", 2 mean "rest", 3 means "first first", etc.
        """
        return to_sexp_f(self.path_for_iter(self.path_iter(), base))

    def first(self):
        return self.__class__(self._index * 2 + 1)

    def rest(self):
        return self.__class__(self._index * 2 + 2)

    def up(self):
        return self.__class__((self._index - 1) >> 1)

    def reset_base(self, new_base):
        """
        Tweak node index where we assume the root node is now pushed down to the
        new_base node location.
        """
        r = new_base
        for d in self.path_iter():
            if d:
                r = r.first()
            else:
                r = r.rest()
        return r

    def __repr__(self):
        return "Node(%d)" % self._index
