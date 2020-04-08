import enum


def i(b):
    return int.from_bytes(b, "big")


class Type(enum.IntEnum):
    CONS = i(b"CONS")

    NULL = i(b"NULL")
    INT = i(b"INT")
    HEX = i(b"HEX")
    QUOTES = i(b"QT")
    DOUBLE_QUOTE = i(b"DQT")
    SINGLE_QUOTE = i(b"SQT")
    SYMBOL = i(b"SYM")

    def listp(self):
        return False

    def as_atom(self):
        return self.to_bytes(len(self), "big", signed=False)

    def __len__(self):
        return (self.bit_length() + 7) >> 3


CONS_TYPES = [Type.CONS]
