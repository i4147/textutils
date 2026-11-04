# -*- coding=utf-8 -*-

import re
import typing as t
from ..structures import Caption
from ..exceptions import *
from ..util import parse_time_dot as parse_time


HEAD_RE = re.compile(r"^WEBVTT ?")
RANGE_RE = re.compile(
    r"^(?P<start>(\d{2,}:)?\d{2}:\d{2}\.\d{3}) --> (?P<end>(\d{2,}:)?\d{2}:\d{2}\.\d{3})"
    r"(?P<style> .*)?$"
)


def read_webvtt(fp: t.TextIO) -> t.List[Caption]:
    captions: t.List[Caption] = []

    lines = (_.rstrip() for _ in fp)

    if HEAD_RE.match(next(lines, "")) is None:
        raise FormatException("Invalid webvtt header")

    for line in lines:
        if not line:
            continue
        elif line.startswith(("STYLE", "NOTE")):
            while next(lines, ""):
                pass
        else:
            id_ = None
            styles = {}

            match = RANGE_RE.fullmatch(line)
            if match is None:
                id_ = line
                line = next(lines, "")
                match = RANGE_RE.fullmatch(line)

            if match is None:
                raise FormatException(f"Missing or invalid time range ({line})")

            start = parse_time(match.group("start"))
            end = parse_time(match.group("end"))

            style: str = match.group("style")

            if style is not None:
                for style in style.split():
                    key, sep, value = style.partition(":")
                    if sep is None:
                        raise FormatException(f"Bad style format ({style})")
                    styles[key] = value

            text_lines = []
            for text_line in lines:
                if not text_line:
                    break
                if text_line.startswith("- "):
                    if text_lines:
                        text_lines[-1] += " " + text_line[2:]
                    else:
                        text_lines.append(text_line[2:])
                else:
                    text_lines.append(text_line)

            captions.append(Caption(start=start, end=end, text=text_lines, id=id_, styles=styles))

    return captions
