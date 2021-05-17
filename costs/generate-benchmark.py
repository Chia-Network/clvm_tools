import os
import random
import sys

def make_value(length):
    ret = '0x'
    for i in range(length):
        ret += '%02x' % ((random.getrandbits(7) << 1) + 1)
    return ret

def make_lookup(depth):
    path = 1
    tree = '42';
    while depth > 0:
        path <<= 1
        leg = random.getrandbits(1)
        if leg == 0:
            tree = '(' + tree + ' . 0x1337)'
        else:
            tree = '(0x1337 . ' + tree + ')'
        path |= leg
        depth -= 1
    return '%d' % path, tree

def generate_args(n, name, value_size, filename):
    ret = '(' + name
    for i in range(n):
        ret += ' (q . ' + make_value(value_size) + ')'
    ret += ')'
    return '%s_args-%d-%d' % (filename, value_size, n), ret, '()'

def generate_nested(n, name, value_size, filename, arity=2):
    ret = ''
    for i in range(n):
        ret += '(%s ' % name
        for i in range(arity - 1):
            ret += '(q . ' + make_value(value_size) + ') '
    ret += '(q . ' + make_value(value_size) + ')'
    for i in range(n):
        ret += ')'
    return '%s_nest-%d-%d' % (filename, value_size, n), ret, '()'

def generate_nested_1(n, name, value_size, filename, arity=2):
    ret = ''
    for i in range(n):
        ret += '(%s ' % name
        for i in range(arity - 1):
            ret += '(q . 1) '
    ret += '(q . ' + make_value(value_size) + ')'
    for i in range(n):
        ret += ')'
    return '%s_nest1-%d-%d' % (filename, value_size, n), ret, '()'

def size_of_value(val):
    if val.startswith('0x'):
        return (len(val) - 2) / 2
    if val.startswith('"') and val.endswith('"'):
        return len(val) - 2
    print("don't know how to interpret value: %s" % val)
    sys.exit(1)

def generate_args_value(n, name, value, filename):
    ret = '(' + name
    for i in range(n):
        ret += ' (q . ' + value + ')'
    ret += ')'
    return '%s_args-%d-%d' % (filename, size_of_value(value), n), ret, '()'

def generate_nested_value(n, name, value, filename, arity=2):
    ret = ''
    for i in range(n):
        ret += '(%s ' % name
        for i in range(arity - 1):
            ret += '(q . ' + value + ') '
    ret += '(q . ' + value + ')'
    for i in range(n):
        ret += ')'
    return '%s_nest-%d-%d' % (filename, size_of_value(value), n), ret, '()'

# use a different value for right hand and left hand. e.g. shift has limits on
# how large the right hand side can be
def generate_nested_2values(n, name, value_sizes, filename, arity=2):
    ret = ''
    for i in range(n):
        ret += '(%s ' % name
    ret += '(q . ' + make_value(value_sizes[0]) + ')'
    for i in range(n):
        for i in range(arity - 1):
            ret += ' (q . ' + make_value(value_sizes[1]) + ')'
        ret += ')'
    return '%s_nest-%d-%d' % (filename, value_sizes[0], n), ret, '()'

def generate_lookup(n):
    path, tree = make_lookup(n)
    return 'lookup-2-%d' % n, path, tree

def generate_lookup_op_list(n):
    path, tree = make_lookup(1)
    ret = ''
    for i in range(n):
        ret += '(c ' + path + ' '
    ret += '()'
    for i in range(n):
        ret += ')'

    return 'lookup_2-2-%d' % n, ret, tree

def generate_op_list(n, name, value_size, filename, arity=2):
    ret = ''
    for i in range(n):
        ret += '(c (%s' % name
        for i in range(arity):
            ret += ' (q . ' + make_value(value_size) + ')'
        ret += ') '
    ret += '()'
    for i in range(n):
        ret += ')'
    return '%s-%d-%d' % (filename, value_size, n), ret, '()'

def generate_list(n, name, filename):
    ret = ''
    for i in range(n):
        ret += '(c (%s (q . (1 2 3))) ' % name
    ret += '()'
    for i in range(n):
        ret += ')'
    return '%s-1-%d' % (filename, n), ret, '()'

def generate_list_empty(n):
    ret = ''
    for i in range(n):
        ret += '(c (q . (1 2 3)) '
    ret += '()'
    for i in range(n):
        ret += ')'
    return 'first_empty-1-%d' % n, ret, '()'

def generate_if(n):
    ret = ''
    # alternate between true and false
    conditions = ['()', '(q . 1)']
    for i in range(n):
        ret += '(c (i %s (q . 1) (q . 2)) ' % conditions[i % 2]
    ret += '()'
    for i in range(n):
        ret += ')'
    return 'if-1-%d' % n, ret, '()'

def gen_apply(n, name):
    folder = 'test-programs/%s' % name
    try: os.mkdir(folder)
    except: pass
    with open(folder + '/%s-%d.clvm' % (name, n), 'w+') as f:
        for i in range(n):
            f.write('(a (q . (lognot ');

        f.write('(q . 1)');

        for i in range(n):
            f.write(')) ())');

    with open(folder + '/%s-%d.env' % (name, n), 'w+') as f:
        f.write('()')

def get_range(name):
    if name.split('-')[0].endswith('_empty'): return 3000,40,[1]
    if name.startswith('mul_nest1'): return 3000,300,[1, 25, 50, 100, 200, 400, 600, 800, 1000]
    if name.startswith('mul'): return 3000,50,[1, 25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400]
    if name.startswith('cons-'): return 3000,40,[1]
    if name.startswith('lookup'): return 3000,40,[2]
    if name.startswith('point_add'): return 300,4,[48]
    if name.startswith('listp'): return 3000,40,[1]
    if name.startswith('first'): return 3000,40,[1]
    if name.startswith('rest'): return 3000,40,[1]
    if name.startswith('if-'): return 3000,40,[1]
    else: return 3000,40,[1, 128, 1024]

def print_files(fun):
    name = fun(0, 1)[0]
    end, step, vsizes = get_range(name)
    folder = 'test-programs/' + name.split('-')[0].split('_')[0]
    try: os.mkdir(folder)
    except: pass
    for value_size in vsizes:
        for i in range(2, end, step):
            name, prg, env = fun(i, value_size)
            open(folder + '/' + name + '.clvm', 'w+').write(prg)
            open(folder + '/' + name + '.env', 'w+').write(env)

try: os.mkdir('test-programs')
except: pass

print_files(lambda n, vs: generate_op_list(n, 'concat', vs, 'concat'))
print_files(lambda n, vs: generate_args(n, 'concat', vs, 'concat'))

print_files(lambda n, vs: generate_op_list(n, 'divmod', vs, 'divmod'))
print_files(lambda n, vs: generate_op_list(n, '/', vs, 'div'))

print_files(lambda n, vs: generate_args(n, '+', vs, 'plus'))
print_files(lambda n, vs: generate_op_list(n, '+', vs, 'plus'))
print_files(lambda n, vs: generate_op_list(n, '+', vs, 'plus_empty', arity=0))

print_files(lambda n, vs: generate_args(n, '-', vs, 'minus'))
print_files(lambda n, vs: generate_op_list(n, '-', vs, 'minus'))
print_files(lambda n, vs: generate_op_list(n, '-', vs, 'minus_empty', arity=0))

print_files(lambda n, vs: generate_args(n, 'logand', vs, 'logand'))
print_files(lambda n, vs: generate_op_list(n, 'logand', vs, 'logand'))
print_files(lambda n, vs: generate_op_list(n, 'logand', vs, 'logand_empty', arity=0))

print_files(lambda n, vs: generate_args(n, 'logior', vs, 'logior'))
print_files(lambda n, vs: generate_op_list(n, 'logior', vs, 'logior'))
print_files(lambda n, vs: generate_op_list(n, 'logior', vs, 'logior_empty', arity=0))

print_files(lambda n, vs: generate_args(n, 'logxor', vs, 'logxor'))
print_files(lambda n, vs: generate_op_list(n, 'logxor', vs, 'logxor'))
print_files(lambda n, vs: generate_op_list(n, 'logxor', vs, 'logxor_empty', arity=0))

print_files(lambda n, vs: generate_nested(n, 'lognot', vs, 'lognot', arity=1))
print_files(lambda n, vs: generate_nested(n, 'not', vs, 'not', arity=1))

print_files(lambda n, vs: generate_nested(n, 'any', vs, 'any'))
print_files(lambda n, vs: generate_args(n, 'any', vs, 'any'))

print_files(lambda n, vs: generate_nested(n, 'all', vs, 'all'))
print_files(lambda n, vs: generate_args(n, 'all', vs, 'all'))

print_files(lambda n, vs: generate_nested_2values(n, 'lsh', [vs, 1], 'lsh'))
print_files(lambda n, vs: generate_nested_2values(n, 'ash', [vs, 1], 'ash'))

print_files(lambda n, vs: generate_op_list(n, '=', vs, 'eq'))
print_files(lambda n, vs: generate_op_list(n, '>', vs, 'gr'))
print_files(lambda n, vs: generate_op_list(n, '>s', vs, 'grs'))

print_files(lambda n, vs: generate_nested(n, 'c', vs, 'cons'))

point_val = '0xb3b8ac537f4fd6bde9b26221d49b54b17a506be147347dae5d081c0a6572b611d8484e338f3432971a9823976c6a232b'
print_files(lambda n, vs: generate_nested_value(n, 'point_add', point_val, 'point_add'))
print_files(lambda n, vs: generate_args_value(n, 'point_add', point_val, 'point_add'))

print_files(lambda n, vs: generate_op_list(n, 'sha256', vs, 'sha', arity=1))
print_files(lambda n, vs: generate_op_list(n, 'sha256', vs, 'sha_empty', arity=0))
print_files(lambda n, vs: generate_args(n, 'sha256', vs, 'sha'))

print_files(lambda n, vs: generate_op_list(n, 'pubkey_for_exp', vs, 'pubkey', arity=1))

print_files(lambda n, vs: generate_lookup(n))
print_files(lambda n, vs: generate_lookup_op_list(n))

print_files(lambda n, vs: generate_op_list(n, 'strlen', vs, 'strlen', arity=1))

print_files(lambda n, vs: generate_op_list(n, '*', vs, 'mul'))
print_files(lambda n, vs: generate_nested_1(n, '*', vs, 'mul'))
print_files(lambda n, vs: generate_op_list(n, '*', vs, 'mul_empty', arity=0))

print_files(lambda n, vs: generate_op_list(n, 'l', vs, 'listp', arity=1))

print_files(lambda n, vs: generate_list(n, 'f', 'first'))
print_files(lambda n, vs: generate_list_empty(n))

print_files(lambda n, vs: generate_list(n, 'r', 'rest'))

print_files(lambda n, vs: generate_if(n))
gen_apply(1000, 'apply')

