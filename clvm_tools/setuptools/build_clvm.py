from distutils.cmd import Command
from distutils import log

from setuptools.dist import Distribution

from clvm_tools.clvmc import compile_clvm


Distribution.clvm_extensions = ()


class build_clvm(Command):
    """ Command for building clvm """

    description = "build clvm extensions"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        file_list = self.distribution.clvm_extensions
        for _ in file_list:
            log.info("build_clvm on %s" % _)
            target = "%s.hex" % _
            compile_clvm(_, target)
