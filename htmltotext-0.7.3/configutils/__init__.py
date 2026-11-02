import contextlib
import os
import sys
from build import build_ext
from config import config

if "setuptools" in sys.modules:
    import setuptools
    from setuptools import Extension, setup

    using_setuptools = True
else:
    import distutils
    from distutils import sysconfig
    from distutils.core import Extension, setup

    using_setuptools = False
if not using_setuptools:
    distutils_customize_compiler = sysconfig.customize_compiler

    def my_customize_compiler(compiler):
        retval = distutils_customize_compiler(compiler)
        with contextlib.suppress(AttributeError, ValueError):
            compiler.compiler_so.remove("-Wstrict-prototypes")
        return retval

    sysconfig.customize_compiler = my_customize_compiler
del os
del sys
