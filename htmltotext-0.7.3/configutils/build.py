import contextlib
import os
import sys
import cPickle

if "setuptools" in sys.modules:
    from setuptools.command.build_ext import build_ext as du_build_ext
else:
    from distutils.command.build_ext import build_ext as du_build_ext


def read_params():
    path = os.path.join("configutils", "params.cache")
    try:
        fd = open(path, "rb")
        stored_params = cPickle.load(fd)
        fd.close()
        return stored_params
    except IOError:
        return {}


class build_ext(du_build_ext):
    def use_param(self, params, param):
        if param not in params:
            return
        val = getattr(self, param, [])
        val.extend(params[param])
        setattr(self, param, val)

    def run(self):
        configpath = os.path.join("src", "config.h")
        paramspath = os.path.join("configutils", "params.cache")
        if not os.path.exists(configpath) or not os.path.exists(paramspath):
            self.run_command("config")
        params = read_params()
        self.use_param(params, "include_dirs")
        self.use_param(params, "library_dirs")
        self.use_param(params, "libraries")
        du_build_ext.run(self)

    def build_extension(self, ext):
        with contextlib.suppress(AttributeError, ValueError):
            self.compiler.compiler_so.remove("-Wstrict-prototypes")
        return du_build_ext.build_extension(self, ext)
