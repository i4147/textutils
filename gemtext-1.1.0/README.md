# gemtext - A simple library for parsing the Gemtext markup language

## Introduction

`gemtext` is a small and simple library that provides code for parsing [the
hypertext markup language of the Gemini
project](https://geminiprotocol.net/docs/gemtext-specification.gmi).

## Installation

`gemtext` is [available from pypi](https://pypi.org/project/gemtext/) and
can be installed with your package installer of choice.

With `pip`:

```shell
pip install gemtext
```

With `uv`:

```shell
uv add gemtext
```

## Quick start

The library provides a single main parsing class called `Gemtext`. It is
initialised with a body of gemtext and the `content` property provides a
list of lines, typed with their parsed type, each having its own relevant
properties.

A very minimal parser might look like this:

```python
import fileinput
from gemtext import Gemtext


def parse_input() -> None:
    for gem_line in Gemtext("".join(fileinput.input())).content:
        print(f"{gem_line!r}")
```

The library contains a simple test command line tool, which can be accessed
either via the Python `-m` switch, or depending on your environment, via the
`gemtext` command. For example, given this content of a file called `example.gmi`:

````text
# This is a heading

## This is a sub-heading

### This is a sub-sub-heading

=> gemini://davep.gemcities.com/ Dave's test capsule

> This is a deep and meaningful quote

```
Here is some pre-formatted text.

Here's some more of that text.
```

* One
* Two
* Three
````

The `gemtext` command (or `python -m gemtext`) would produce:

```sh
$ gemtext example.gmi
Heading(content='This is a heading', level=1)
Paragraph(content='')
Heading(content='This is a sub-heading', level=2)
Paragraph(content='')
Heading(content='This is a sub-sub-heading', level=3)
Paragraph(content='')
Link(content="Dave's test capsule", uri='gemini://davep.gemcities.com/')
Paragraph(content='')
Quote(content='This is a deep and meaningful quote')
Paragraph(content='')
PreFormatted(content="Here is some pre-formatted text.\n\nHere's some more of that text.")
Paragraph(content='')
ListItem(content='One')
ListItem(content='Two')
ListItem(content='Three')
```

See [the main documentation](https://gemtext.davep.dev/) for the full API.

[//]: # (README.md ends here)
