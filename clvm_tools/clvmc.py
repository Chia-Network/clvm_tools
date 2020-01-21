# clvm_tools setuptools integration

from distutils import log
from distutils.dep_util import newer

import os
import pathlib

import stage_2

from ir import reader
from clvm_tools import binutils


def build_clvm_hex(path):

    output_path = "%s.hex" % path
    if newer(path, output_path):

        log.info("clvm compiling %s" % path)
        with open(path) as f:
            text = f.read()
        ir_src = reader.read_ir(text)
        assembled_sexp = binutils.assemble_from_ir(ir_src)

        input_sexp = assembled_sexp.to((assembled_sexp, []))
        eval_cost = stage_2.EVAL_COST
        cost, result = eval_cost(eval_cost, stage_2.run, input_sexp)
        hex = result.as_bin().hex()

        with open(output_path, "w") as f:
            f.write(hex)

    return output_path


def find_files(path=""):
    r = []
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".clvm"):
                full_path = pathlib.Path(dirpath, filename)
                target = build_clvm_hex(full_path)
                r.append(target)
    return r
