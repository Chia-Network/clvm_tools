from .build_clvm import build_clvm  # noqa
from .patch_build_ext import patch_build_ext
from .patched_build_ext import build_ext


def monkey_patch():
    patch_build_ext(build_ext)
