#!/usr/bin/env python

from setuptools import setup

with open("README.md", "rt") as fh:
    long_description = fh.read()

dependencies = [
    "clvm>=0.9.2",
    "clvm_tools_rs>=0.1.37",
    "importlib_metadata",
    "setuptools",
]

dev_dependencies = [
    "pytest",
]

setup(
    name="clvm_tools",
    packages=[
        "ir",
        "clvm_tools",
        "clvm_tools.setuptools",
        "stages",
        "stages.stage_2",
    ],
    author="Chia Network, Inc.",
    entry_points={
        "console_scripts": [
            "read_ir = clvm_tools.cmds:read_ir",
            "opc = clvm_tools.cmds:opc",
            "opd = clvm_tools.cmds:opd",
            "run = clvm_tools.cmds:run",
            "brun = clvm_tools.cmds:brun",
        ],
    },
    package_data={
        "": ["py.typed"],
    },
    author_email="hello@chia.net",
    install_requires=dependencies,
    url="https://github.com/Chia-Network",
    license="Apache-2.0",
    description="CLVM compiler.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Security :: Cryptography",
    ],
    extras_require=dict(
        dev=dev_dependencies,
    ),
    project_urls={
        "Bug Reports": "https://github.com/Chia-Network/clvm_tools",
        "Source": "https://github.com/Chia-Network/clvm_tools",
    },
)
