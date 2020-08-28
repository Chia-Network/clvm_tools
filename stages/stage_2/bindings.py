from clvm_tools import binutils


brun = binutils.assemble("((c 2 3))")
run = binutils.assemble("((c (opt (com (f 1))) (r 1)))")
