# -*- coding=utf-8 -*-

import io
import typing as t
from os import PathLike
from ..structures import Caption
from ..util import format_ts_dot as format_ts


def write_subviewer(captions: t.Iterable[Caption], fp: t.TextIO) -> None:

    for i, caption in enumerate(captions):
        if i != 0:
            fp.write("\r\n")

        fp.write(f"{format_ts(caption.start)},{format_ts(caption.end)}\r\n")
        text = caption.text.replace("\n", "[br]")
        fp.write(f"{text}\r\n")
