from distutils import log
from setuptools.command.build_ext import build_ext as _build_ext


class build_ext(_build_ext):

    def __init__(self, *args):
        _build_ext.__init__(self, *args)

    def has_clvm_extensions(self):
        return (
            self.distribution.clvm_extensions
            and len(self.distribution.clvm_extensions) > 0
        )

    def check_extensions_list(self, extensions):
        if extensions:
            _build_ext.check_extensions_list(self, extensions)

    def run(self):
        """Run build_clvm sub command """
        if self.has_clvm_extensions():
            log.info("running build_clvm")
            build_clvm = self.get_finalized_command("build_clvm")
            build_clvm.inplace = self.inplace
            build_clvm.run()

        _build_ext.run(self)
