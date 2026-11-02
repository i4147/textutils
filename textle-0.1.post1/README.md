# `textle`
[![Documentation Status](https://readthedocs.org/projects/textle/badge/?version=latest)](https://textle.readthedocs.io/en/latest/?badge=latest) ![PyPI - License](https://img.shields.io/pypi/l/textle.svg) [![PyPI](https://img.shields.io/pypi/v/textle.svg?color=orange)](https://pypi.org/project/textle/)

![logo](docs/img/logo.png)

`textle` is software to automate the use of typesetting and their support tools, like `LaTeX` and `pandoc`.

## Usage

[![usage example](https://asciinema.org/a/opmSpftGOmDFBJGWHhYvXu2BT.svg)](https://asciinema.org/a/opmSpftGOmDFBJGWHhYvXu2BT)

For more information, see the full documentation on [read the docs](https://textle.readthedocs.io), or in the `docs/` folder.

## Installation

```
$ # textle is python3 only
$ pip3 install textle
```

Alternatively, install from source by cloning this repo and using

```
$ python3 setup.py install
```

To build the documentation to the `site` folder, 

```
$ mkdocs build
```

## Why

This tool was created as I often create small one-off TeX (sometimes from markdown through pandoc) projects that need to be formatted in similar ways, and that I like building quickly.
`textle` aims to solve these problems: it makes it easy to not only build a project to a PDF once, but even to do it live; and it makes simple the definition of the project. All one has to 
do is either use the CLI, which was designed to be powerful and simple, or write a `Textlefile`. The project also aimed to be lightweight, both binary-wise and filesystem-wise, the idea being to 
not pollute a VCS with random files.

The Usage section demonstrates my common use cases.

## Licensing

The logo is licensed under the [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

This project is licensed under the MIT License, see `LICENSE` for more information.
