# -*- coding=utf-8 -*-

import re
from ..exceptions import FormatException


__all__ = [
    "parse_time_dot",
    "parse_time_comma",
    "parse_time_any",
    "format_ts_dot",
    "format_ts_comma",
]


TIME_DOT_RE = re.compile(r"(?:(?P<h>\d{2,}):)?(?P<m>\d{2}):(?P<s>\d{2}\.\d{3})")
TIME_COMMA_RE = re.compile(r"(?P<h>\d{2,}):(?P<m>\d{2}):(?P<s>\d{2},\d{3})")

TIME_ANY_RE = re.compile(r"(?:(?:(?P<h>\d+):)?(?P<m>\d+):)?(?P<s>\d+(?:[.,]\d+)?)")


def parse_time_dot(text: str) -> float:
    match = TIME_DOT_RE.fullmatch(text)
    if match is None:
        raise FormatException(f"Bad time format: {text!r}")

    hours = match.group("h")
    hours = 0 if hours is None else int(hours)
    minutes = int(match.group("m"))
    seconds = float(match.group("s"))
    return (hours * 3600) + (minutes * 60) + seconds


def parse_time_comma(text: str) -> float:
    match = TIME_COMMA_RE.fullmatch(text)
    if match is None:
        raise FormatException(f"Bad time format: {text!r}")

    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = float(match.group("s").replace(",", "."))
    return (hours * 3600) + (minutes * 60) + seconds


def parse_time_any(text: str) -> float:
    match = TIME_ANY_RE.fullmatch(text)
    if match is None:
        raise ValueError(f"Bad time format: {text!r}")

    hours = match.group("h")
    hours = 0 if hours is None else int(hours)
    minutes = match.group("m")
    minutes = 0 if minutes is None else int(minutes)
    seconds = float(match.group("s").replace(",", "."))
    return (hours * 3600) + (minutes * 60) + seconds


def format_ts_dot(ts: float) -> str:
    seconds = ts % 60
    minutes = int((ts / 60) % 60)
    hours = int(ts / 3600)

    return f"{hours:0>2}:{minutes:0>2}:{format(seconds, '.3f'):0>6}"


def format_ts_comma(ts: float) -> str:
    seconds = ts % 60
    minutes = int((ts / 60) % 60)
    hours = int(ts / 3600)

    return f"{hours:0>2}:{minutes:0>2}:{format(seconds, '.3f').replace('.', ','):0>6}"
