# -*- coding=utf-8 -*-

from pathlib import Path
from . import load, dump


def cmd_read(input_fp, after: float = None, before: float = None, **kwargs) -> None:
    input_fp = Path(input_fp)
    if not input_fp.is_file():
        raise FileNotFoundError(str(input_fp))

    for caption in load(input_fp, **kwargs):
        if after and caption.start <= after:
            continue
        if before and caption.end >= before:
            continue
        print(f"{caption!r}")


def cmd_convert(input_fp: str, output_fp: str, overwrite: bool = False, **kwargs):
    input_fp = Path(input_fp)
    if not input_fp.is_file():
        raise FileNotFoundError(str(input_fp))
    output_fp = Path(output_fp)
    if output_fp.is_file():
        if not overwrite:
            raise FileExistsError(str(output_fp))
    elif output_fp.exists():
        raise RuntimeError(f"{output_fp!s} can't be overwritten")

    input_kwargs = {key[6:]: value for key, value in kwargs.items() if key.startswith("input_")}
    output_kwargs = {key[7:]: value for key, value in kwargs.items() if key.startswith("output_")}

    captions = load(input_fp, **input_kwargs)
    dump(captions, output_fp, **output_kwargs)
