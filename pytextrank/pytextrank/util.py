# -*- coding: utf-8 -*-

import itertools
import re
import string
import typing
import unicodedata

from spacy.tokens import Span


def groupby_apply(
    data: typing.Iterable[typing.Any],
    keyfunc: typing.Callable,
    applyfunc: typing.Callable,
) -> typing.List[typing.Tuple[typing.Any, typing.Any]]:
    data = sorted(data, key=keyfunc)

    accum: typing.List[typing.Tuple[typing.Any, typing.Any]] = [
        (
            k,
            applyfunc(g),
        )
        for k, g in itertools.groupby(data, keyfunc)
    ]

    return accum


def default_scrubber(span: Span) -> str:
    return span.text.replace("'", "")


def maniacal_scrubber(span: Span) -> str:
    text = span.text

    if type(text).__name__ != "str":
        print("not a string?", type(text), text)

    x = " ".join(map(lambda s: s.strip(), text.split("\n"))).strip()

    x = x.replace("“", '"').replace("”", '"')
    x = x.replace("‘", "'").replace("’", "'").replace("`", "'")
    x = x.replace("…", "...").replace("–", "-")

    x = str(unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("utf-8"))

    return x


def split_grafs(lines: typing.List[str]) -> typing.Iterator[str]:
    graf: typing.List[str] = []

    for line in lines:
        line = line.strip()

        if len(line) < 1:
            if len(graf) > 0:
                yield "\n".join(graf)
                graf = []
        else:
            graf.append(line)

    if len(graf) > 0:
        yield "\n".join(graf)


def filter_quotes(
    text: str,
    *,
    is_email: bool = True,
) -> typing.List[str]:
    _PAT_FORWARD = re.compile(r"\n-+ Forwarded message -+\n")
    _PAT_REPLIED = re.compile(r"\nOn.*\d+.*\n?wrote\:\n+\>")
    _PAT_UNSUBSC = re.compile(r"\n-+\nTo unsubscribe,.*\nFor additional commands,.*")

    if is_email:
        text = str(filter(lambda x: x in string.printable, text))

        m = _PAT_FORWARD.split(text, re.M)

        if m and len(m) > 1:
            text = m[0]

        m = _PAT_REPLIED.split(text, re.M)

        if m and len(m) > 1:
            text = m[0]

        m = _PAT_UNSUBSC.split(text, re.M)

        if m:
            text = m[0]

    lines: typing.List[str] = []

    for line in text.split("\n"):
        if line.startswith(">"):
            lines.append("")
        else:
            lines.append(line)

    return list(split_grafs(lines))
