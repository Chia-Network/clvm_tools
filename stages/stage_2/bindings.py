from clvm_tools import binutils


brun = binutils.assemble("((a))")
run = binutils.assemble("((c (opt (com (f 1))) (r 1)))")
