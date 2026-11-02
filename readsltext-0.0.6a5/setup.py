from codecs import open
from os import path
from setuptools import setup, find_packages
from readsltext.readsltext import (
    __projectname__,
    __version__,
    __author__,
    __email__,
    __license__,
    __licensepypi__,
    __statuspypi__,
)

HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.rst"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()
setup(
    name=__projectname__,
    url="https://github.com/suizokukan/readsltext",
    version=__version__,
    description="GPLv3/Python3/CLI text format to annotate texts and produce easy-to-read versions of them",
    long_description=LONG_DESCRIPTION,
    author=__author__,
    author_email=__email__,
    license=__license__,
    classifiers=[
        __statuspypi__,
        "Intended Audience :: Education",
        "Topic :: Utilities",
        __licensepypi__,
        "Programming Language :: Python :: 3",
    ],
    keywords="language text",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "readsltext=readsltext.readsltext:clientrypoint",
        ],
    },
)
