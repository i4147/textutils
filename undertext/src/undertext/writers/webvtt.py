# -*- coding=utf-8 -*-

import typing as t
from ..structures import Caption
from ..util import format_ts_dot as format_ts


def write_webvtt(captions: t.Iterable[Caption], fp: t.TextIO, header: str = None) -> None:
    fp.write("WEBVTT")
    if header is not None:
        fp.write(f" - {header}")
    fp.write("\r\n")

    for caption in captions:
        fp.write("\r\n")
        if caption.id:
            fp.write(f"{caption.id}\r\n")
        fp.write(f"{format_ts(caption.start)} --> {format_ts(caption.end)}")
        if caption.styles:
            fp.write(" ")
            for key, value in caption.styles.items():
                fp.write(f"{key}:{value}")
        fp.write("\r\n")
        if len(caption.lines) == 1:
            fp.write(f"{caption.text}\r\n")
        else:
            for line in caption.lines:
                fp.write(f"- {line}\r\n")
