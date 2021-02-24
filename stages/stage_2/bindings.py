from clvm_tools import binutils


brun = binutils.assemble("(a 2 3)")
run = binutils.assemble("(a (opt (com 2)) 3)")
