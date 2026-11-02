from __future__ import absolute_import, annotations

__version__ = "0.2.0"
from setuptools import find_packages, setup

doclines = __doc__.splitlines()
name, short_description = doclines[0].split(": ")
long_description = "\n".join(doclines[2:])
classifiers = [
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Natural Language :: English",
    "Programming Language :: Python",
]
setup(
    name=name,
    version=__version__,
    description=short_description,
    author="Michael Hoffman",
    author_email="michael.hoffman@utoronto.ca",
    license="GNU GPLv2",
    classifiers=classifiers,
    long_description=long_description,
    package_dir={"": "lib"},
    py_modules=["tabdelim", "textinput"],
    scripts=[
        "scripts/innerjoin",
        "scripts/filter",
        "scripts/nohead",
        "scripts/mean",
        "scripts/hidehead",
        "scripts/intersect",
    ],
    zip_safe=True,
)
