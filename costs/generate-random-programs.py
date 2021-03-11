import random
import os
import sys
from enum import Enum

def make_small_value():
    # we use small values as divisors, so it can't be 0
    return '0x%02x' % random.randint(1, 255)

def make_string():
    length = random.randint(5, 10)
    ret = '"'
    for i in range(length):
        ret += chr(random.randint(ord('A'), ord('Z')))
    ret += '"'
    return ret

def make_value():
    r = random.randint(0, 5)
    if r == 0: return make_string()
    length = random.randint(1, 10)
    ret = '0x'
    for i in range(length):
        ret += '%02x' % random.getrandbits(8)
    return ret

def make_point():
        return random.choice([
'0xb3b8ac537f4fd6bde9b26221d49b54b17a506be147347dae5d081c0a6572b611d8484e338f3432971a9823976c6a232b',
'0x8a9970d47a86db8a2261954a6876081722e347912875a96220db69c23be8b48ac2563499f2a4dc9c50fe169615a77d80',
'0xa7e04cdd823ee4d767e99d72f9f73f5795faaf8161ddef3c3433c11793a27526a1909f8618edea2f01899536dca43d90',
'0x92f552fab78a3c4a0f13297b96c56a7ae83dace9569ec65b94c7dc82490091803f01df688629e998894d8a195cba5c23'])

def make_tree(depth):
    if depth == 1:
        return make_value()
    else:
        return '(' + make_tree(depth - 1) + ' . ' + make_tree(depth - 1) + ')'

def make_path(depth):
    ret = 1
    while depth > 1:
        ret <<= 1
        ret |= random.getrandbits(1)
        depth -= 1
    return '%d' % ret

class ExpType(Enum):
    VALUE = 0
    SMALL_VALUE = 1
    LIST = 2
    VALUE_LIST = 3
    PROGRAM = 4
    POINT = 5
    STRING = 6
    ANYTHING = 7

def make_condition(depth, env_depth):
    r = random.randint(0, 5)

    if r == 3:
        return make_expression(depth - 1, env_depth, ExpType.VALUE)
    elif r == 4:
        return '(l ' + make_expression(depth -1, env_depth) + ')'
    elif r == 5:
        return '(q . ' + make_small_value() + ')'
    elif r == 0:
        ret = '(= '
    elif r == 1:
        ret = '(> '
    elif r == 2:
        ret = '(>s '

    ret += make_expression(depth - 1, env_depth, ExpType.VALUE) + \
        ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ')'
    return ret

def make_expression(depth, env_depth, kind = ExpType.ANYTHING):
    if depth <= 0:
        if kind == ExpType.SMALL_VALUE:
            return '(q . ' + make_small_value() + ')'
        elif kind == ExpType.VALUE:
            return '(q . ' + make_value() + ')'
        elif kind == ExpType.LIST or kind == ExpType.VALUE_LIST or kind == ExpType.ANYTHING:
            return '(q . (' + make_value() + ' ' + make_value() + '))'
        elif kind == ExpType.POINT:
            return '(q . ' + make_point() + ')'
        elif kind == ExpType.STRING:
            return '(q . ' + make_string() + ')'
        else:
            return '(q . (q . ' + make_value() + '))'

    value_kind = ExpType.VALUE

    if kind == ExpType.VALUE:
        r = random.choice([0, 1, 3, 5, 25, 26, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38])
    elif kind == ExpType.SMALL_VALUE:
        value_kind = ExpType.SMALL_VALUE
        r = random.choice([5, 25, 26, 11, 12, 17, 18, 19, 20, 23, 24, 28, 35, 36, 37, 28])
    elif kind == ExpType.POINT:
        r = random.choice([5, 25, 26, 29, 31, 31])
    elif kind == ExpType.STRING:
        r = random.choice([5, 16, 25, 26, 33])
    elif kind == ExpType.LIST:
        r = random.choice([2, 5, 25, 26, 7, 8, 13])
    elif kind == ExpType.VALUE_LIST:
        r = random.choice([5, 25, 26, 7, 8, 13])
    elif kind == ExpType.PROGRAM:
        r = random.choice([5, 25, 26, 9])
    else:
        r = random.randint(0, 38)

    if r == 0:
        # value
        return '(q . ' + make_value() + ')'
    elif r == 1:
        # path
        return make_path(env_depth)
    elif r == 2:
        # cons
        return '(c ' + make_expression(depth - 1, env_depth) + ' ' + make_expression(depth - 1, env_depth, ExpType.LIST) + ')'
    elif r == 3:
        # first (resulting in a value)
        return '(f ' + make_expression(depth - 1, env_depth, ExpType.VALUE_LIST) + ')'
    elif r == 4:
        # rest
        return '(r ' + make_expression(depth - 1, env_depth, ExpType.LIST) + ')'
    elif r == 5 or r == 25 or r == 26:
        # if-condition
        return '(i ' + make_condition(depth - 1, env_depth) + \
            ' ' + make_expression(depth - 1, env_depth, kind) + \
            ' ' + make_expression(depth - 1, env_depth, kind) + ')'
    elif r == 6:
        # first (resulting in anything)
        return '(f ' + make_expression(depth - 1, env_depth, ExpType.LIST) + ')'
    elif r == 7:
        # cons (resulting in a value list)
        return '(c ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + \
            ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE_LIST) + ')'
    elif r == 8:
        # value list
        return '(q . (' + make_value() + ' ' + make_value() + '))'
    elif r == 9 or r == 10:
        # eval
        new_env_depth = random.randint(1, 5)
        return '(a (q . ' + make_expression(depth - 1, new_env_depth) + ') (q . ' + make_tree(new_env_depth) + '))'
    elif r == 11:
        # add expression
        ret = '(+'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, value_kind)
        return ret + ')'
    elif r == 12:
        # subtract expression
        ret = '(-'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, value_kind)
        return ret + ')'
    elif r == 13:
        # divmod expression
        return '(divmod ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ' (q . ' + \
            make_small_value() + '))'
    elif r == 14:
        # divmod expression, integer division
        return '(f (divmod ' + make_expression(depth - 1, env_depth, value_kind) + ' (q . ' + \
            make_small_value() + ')))'
    elif r == 15:
        # divmod expression, remainder
        return '(r (divmod ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ' (q . ' + \
            make_small_value() + ')))'
    elif r == 16:
        # concat expression
        ret = '(concat'
        n = random.randint(1, 4)
        for i in range(n):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE)
        ret += ' (q . ' + make_string() + ')'
        return ret + ')'
    elif r == 17:
        # logical or
        ret = '(logior'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, value_kind)
        return ret + ')'
    elif r == 18:
        # logical xor
        ret = '(logxor'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, value_kind)
        return ret + ')'
    elif r == 19:
        # logical and
        ret = '(logand'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, value_kind)
        return ret + ')'
    elif r == 20:
        # logical not
        return '(lognot ' + make_expression(depth - 1, env_depth, value_kind) + ')'
    elif r == 21:
        # arithmetic shift
        return '(ash ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ' ' + \
            make_expression(depth - 1, env_depth, ExpType.SMALL_VALUE) + ')'
    elif r == 22:
        # left shift
        return '(lsh ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ' ' + \
            make_expression(depth - 1, env_depth, ExpType.SMALL_VALUE) + ')'
    elif r == 23:
        # strlen
        return '(strlen ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ')'
    elif r == 24:
        return '(q . ' + make_small_value() + ')'
    elif r == 27:
        # multiply expression
        ret = '(*'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE)
        return ret + ')'
    elif r == 28:
        # listp
        return '(l ' + make_expression(depth - 1, env_depth) + ')'
    elif r == 29:
        # pubkey_for_exp
        return '(pubkey_for_exp ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ')'
    elif r == 30:
        # a valid point
       return '(q . ' + make_point() + ')'
    elif r == 31:
        # point_add
        ret = '(point_add'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.POINT)
        return ret + ')'
    elif r == 32:
        # substring
        return '(substr ' + make_expression(depth - 1, env_depth, ExpType.STRING) + ' (q . 0) (q . 1))';
    elif r == 33:
        return '(q . ' + make_string() + ')'
    elif r == 34:
        ret = '(sha256'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE)
        return ret + ')'
    elif r == 35:
        ret = '(any'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE)
        return ret + ')'
    elif r == 36:
        ret = '(all'
        for i in range(random.randint(0, 4)):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE)
        return ret + ')'
    elif r == 37:
        return '(not ' + make_expression(depth - 1, env_depth, ExpType.VALUE) + ')'
    elif r == 38:
        # concat expression (may return an empty string)
        ret = '(concat'
        n = random.randint(0, 4)
        for i in range(n):
            ret += ' ' + make_expression(depth - 1, env_depth, ExpType.VALUE)
        return ret + ')'

    print('ERROR: r=%d' % r)

left_to_generate = 1000

try: os.mkdir('mixed-programs')
except: pass

if len(sys.argv) > 1:
    seed = int(sys.argv[1])
    left_to_generate = 1
else:
    seed = random.getrandbits(32)

while left_to_generate > 0:
    left_to_generate -= 1
    random.seed(seed)

    env_depth = random.randint(1, 10)
    depth = random.randint(16, 20)

    print('seed:', seed)

    program = make_expression(depth, env_depth)
    arguments = make_tree(env_depth)
    filename = 'mixed-programs/mixed-%08x.clvm' % seed
    env_filename = 'mixed-programs/mixed-%08x.env' % seed
    prg = open(filename, 'w+').write(program)
    env_file = open(env_filename, 'w+').write(arguments)

    seed = random.getrandbits(32)
