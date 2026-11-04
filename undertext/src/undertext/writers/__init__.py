# -*- coding=utf-8 -*-

import typing as t
from os import PathLike
from pathlib import Path
from ..structures import Caption
from .microdvd import write_microdvd
from .subrip import write_subrip
from .subviewer import write_subviewer
from .webvtt import write_webvtt


EXT_MAP = dict(
    sbv=write_subviewer,
    srt=write_subrip,
    sub=write_microdvd,
    vtt=write_webvtt,
)
ALIAS_MAP = dict(
    microdvd=write_microdvd,
    subrip=write_subrip,
    subviewer=write_subviewer,
    webvtt=write_webvtt,
)


def dump(captions: t.Iterable[Caption], fp: t.Union[str, PathLike, t.TextIO], fmt: str = None, **kwargs) -> None:
    fp = Path(fp)

    if fmt is None:
        fmt = fp.suffix[1:].lower()
        writer = EXT_MAP.get(fmt)
    else:
        fmt = fmt.lower()
        writer = ALIAS_MAP.get(fmt) or EXT_MAP.get(fmt)

    if writer is None:
        raise ValueError(f"Unknown format ({fmt!s})")

    if isinstance(fp, t.TextIO):
        writer(captions, fp, **kwargs)
    else:
        with open(fp, "w") as f:
            writer(captions, f, **kwargs)


def dumps(captions: t.Iterable[Caption], fmt: str, **kwargs) -> str:
    from io import StringIO

    fmt = fmt.lower()
    writer = ALIAS_MAP.get(fmt) or EXT_MAP.get(fmt)
    if writer is None:
        raise ValueError(f"Unknown format ({fmt!s})")

    with StringIO() as out:
        writer(captions, out, **kwargs)
        return out.getvalue()
