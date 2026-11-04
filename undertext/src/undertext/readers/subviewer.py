# -*- coding=utf-8 -*-

import re
import typing as t
from pathlib import Path
from ..structures import Caption
from ..exceptions import *
from ..util import parse_time_dot as parse_time


RANGE_RE = re.compile(r"^(?P<start>(\d{2,}:)?\d{2}:\d{2}.\d{3}),(?P<end>(\d{2,}:)?\d{2}:\d{2}.\d{3})$")


def read_subviewer(fp: t.TextIO) -> t.List[Caption]:
    captions: t.List[Caption] = []

    lines = (_.rstrip() for _ in fp)

    for line in lines:
        match = RANGE_RE.fullmatch(line)
        if match is None:
            raise FormatException(f"Missing or invalid time range ({line})")

        start = parse_time(match.group("start"))
        end = parse_time(match.group("end"))

        text_line = next(lines, "")
        text_lines = text_line.split("[br]")

        captions.append(Caption(start=start, end=end, text=text_lines))

        next(lines, "")

    return captions
