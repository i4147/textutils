# -*- coding=utf-8 -*-

import re
import typing as t
from ..structures import Caption
from ..exceptions import *
from ..util import parse_time_comma as parse_time


RANGE_RE = re.compile(
    r"^(?P<start>(\d{2,}:)?\d{2}:\d{2},\d{3}) --> (?P<end>(\d{2,}:)?\d{2}:\d{2},\d{3})"
    r"(?P<style> .*)?$"
)


def read_subrip(fp: t.TextIO) -> t.List[Caption]:
    captions: t.List[Caption] = []

    lines = (_.rstrip() for _ in iter(fp))

    i = 0

    for line in lines:
        i += 1
        if line != f"{i}":
            raise FormatException("Bad numeric counter")

        line = next(lines, "")
        match = RANGE_RE.fullmatch(line)
        if match is None:
            raise FormatException(f"Missing or invalid time range ({line})")

        start = parse_time(match.group("start"))
        end = parse_time(match.group("end"))

        text_lines = []
        for text_line in lines:
            if not text_line:
                break
            text_lines.append(text_line)

        captions.append(Caption(start=start, end=end, text=text_lines))

    return captions
