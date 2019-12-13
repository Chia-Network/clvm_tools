#!/usr/bin/env python

from setuptools import setup

from clvm_tools.version import version

setup(
    name="clvm_tools",
    version=version,
    packages=[
        "ir",
        "clvm_tools",
        "stage_2",
    ],
    author="Chia Network, Inc.",

    entry_points={
        'console_scripts':
            [
                'read_ir = clvm_tools.cmds:read_ir',
                'opc = clvm_tools.cmds:opc',
                'opd = clvm_tools.cmds:opd',
                'run = clvm_tools.cmds:run',
                'brun = clvm_tools.cmds:brun',
            ],
        "setuptools.file_finders": ["clvmc = clvm_tools.clvmc:find_files", ],
        },
    author_email="kiss@chia.net",
    url="https://github.com/Chia-Network",
    license="https://opensource.org/licenses/Apache-2.0",
    description="CLVM compiler.",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Security :: Cryptography',
    ],)
