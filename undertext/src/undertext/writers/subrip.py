# -*- coding=utf-8 -*-

import typing as t
from ..structures import Caption
from ..util import format_ts_comma as format_ts


def write_subrip(captions: t.Iterable[Caption], fp: t.TextIO) -> None:
    for i, caption in enumerate(captions):
        if i != 0:
            fp.write("\r\n")

        fp.write(f"{i + 1}\r\n")
        fp.write(f"{format_ts(caption.start)} --> {format_ts(caption.end)}\r\n")
        for line in caption.lines:
            fp.write(f"{line}\r\n")
