from setuptools import setup

modules = ["bbtext"]
install_requires = ["click>=8.0.4,<9.0.0", "pdfminer.six>=20211012,<20211013"]
entry_points = {"console_scripts": ["bbtext = bbtext:main"]}
setup_kwargs = {
    "name": "bbtext",
    "version": "0.1.0",
    "description": "",
    "long_description": None,
    "author": "Yuta Taniguchi",
    "author_email": "yuta.taniguchi.y.t@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": None,
    "py_modules": modules,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.10,<4.0",
}
setup(**setup_kwargs)
