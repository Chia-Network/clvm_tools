from setuptools_scm import get_version

try:
    __version__ = get_version()
except LookupError:
    __version__ = "unknown"
