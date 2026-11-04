# -*- coding=utf-8 -*-

import typing as t
from os import PathLike
from pathlib import Path
from ..structures import Caption
from .microdvd import read_microdvd
from .subrip import read_subrip
from .subviewer import read_subviewer
from .webvtt import read_webvtt


__all__ = ["load", "loads"]


EXT_MAP = dict(
    sbv=read_subviewer,
    srt=read_subrip,
    sub=read_microdvd,
    vtt=read_webvtt,
)
ALIAS_MAP = dict(
    microdvd=read_microdvd,
    subrip=read_subrip,
    subviewer=read_subviewer,
    webvtt=read_webvtt,
)


def load(fp: t.Union[str, PathLike], fmt: str = None, **kwargs) -> t.List[Caption]:
    fp = Path(fp)

    if fmt is None:
        fmt = fp.suffix[1:]

    with open(fp, "r") as f:
        return loads(buffer=f, fmt=fmt, **kwargs)


def loads(buffer: t.Union[str, t.TextIO], fmt: str, **kwargs) -> t.List[Caption]:
    fmt = fmt.lower()
    reader = ALIAS_MAP.get(fmt) or EXT_MAP.get(fmt)
    if reader is None:
        raise ValueError(f"Unknown format ({fmt!s})")

    if isinstance(buffer, str):
        from io import StringIO

        buffer = StringIO(buffer)

    return reader(buffer, **kwargs)
