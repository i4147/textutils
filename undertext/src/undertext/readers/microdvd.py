# -*- coding=utf-8 -*-

import re
import warnings
import typing as t
from os import PathLike
from ..structures import Caption
from ..exceptions import *


SPLIT_RE = re.compile(r"^\{(?P<start>\d+)}\{(?P<end>\d+)}(?P<text>.+)$")


def read_microdvd(fp: t.TextIO, fps: int = None) -> t.List[Caption]:
    if fps is None:
        warnings.warn(
            "Missing fps specification for reading MicroDVD.\n"
            "MicroDVD works with frames instead of timestamps. "
            "Specify fps to convert frames to timestamps or set to 1 to keep.",
            RuntimeWarning,
        )
        fps = 1

    captions: t.List[Caption] = []

    lines = (_.rstrip() for _ in fp)
    for line in lines:
        if not line:
            continue
        match = SPLIT_RE.fullmatch(line)
        if match is None:
            raise FormatException(f"invalid microdvd line ({line})")
        start = int(match.group("start")) / fps
        end = int(match.group("end")) / fps
        text = match.group("text").split("|")
        captions.append(Caption(start=start, end=end, text=text))

    return captions
