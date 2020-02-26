#!/usr/bin/env python

from setuptools import setup


setup(
    name="clvm_tools",
    packages=["ir", "clvm_tools", "clvm_tools.setuptools", "stages", "stages.stage_2",],
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
    author_email="kiss@chia.net",
    install_requires=["setuptools_scm"],
    setup_requires=["setuptools_scm"],
    use_scm_version={"fallback_version": "unknown"},
    url="https://github.com/Chia-Network",
    license="https://opensource.org/licenses/Apache-2.0",
    description="CLVM compiler.",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Security :: Cryptography",
    ],
    project_urls={
        "Bug Reports": "https://github.com/Chia-Network/clvm_tools",
        "Source": "https://github.com/Chia-Network/clvm_tools",
    },
)
