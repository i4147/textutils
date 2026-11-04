from __future__ import annotations

import re
from typing import Any


WORD_IDENTIFIER: str = r"([A-Za-z_]\w*)"

FILTER_VALUE: str = r"([\w.:-]+)"

ISO_DATE: str = r"\d{4}-\d{2}-\d{2}"

SPURIOUS_FILTER_VALUES: frozenset[str] = frozenset({"where", "with", "and", "or", "for", "of", "in", "is"})

AND_TOKEN: str = " and "


_RE_GTE = re.compile(rf"\b{WORD_IDENTIFIER}\s*>=\s*{FILTER_VALUE}\b")
_RE_LTE = re.compile(rf"\b{WORD_IDENTIFIER}\s*<=\s*{FILTER_VALUE}\b")
_RE_GT = re.compile(rf"\b{WORD_IDENTIFIER}\s*>\s*{FILTER_VALUE}\b")
_RE_LT = re.compile(rf"\b{WORD_IDENTIFIER}\s*<\s*{FILTER_VALUE}\b")

_RE_GREATER_THAN = re.compile(rf"\b{WORD_IDENTIFIER}\s+greater than\s+{FILTER_VALUE}\b")
_RE_LESS_THAN = re.compile(rf"\b{WORD_IDENTIFIER}\s+less than\s+{FILTER_VALUE}\b")
_RE_AFTER = re.compile(rf"\b{WORD_IDENTIFIER}\s+after\s+{FILTER_VALUE}\b")
_RE_BEFORE = re.compile(rf"\b{WORD_IDENTIFIER}\s+before\s+{FILTER_VALUE}\b")

_RE_NEGATION = re.compile(rf"\b{WORD_IDENTIFIER}\s*(?:!=|is not|not)\s*{FILTER_VALUE}\b")

_RE_BETWEEN = re.compile(rf"\b([A-Za-z_]+)\s+between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)")

_RE_BETWEEN_DATES = re.compile(rf"\b([A-Za-z_][A-Za-z0-9_]*)\s+between\s+({ISO_DATE})\s+and\s+({ISO_DATE})\b")

_RE_IN = re.compile(r"\b([a-zA-Z_]+)\s+in\s+([a-zA-Z0-9_,\s]+)")

_RE_DATE_RANGE = re.compile(rf"\b{WORD_IDENTIFIER}\s+from\s+({ISO_DATE})\s+to\s+({ISO_DATE})\b")

_RE_OWNED_ASSET_PATTERNS = (
    re.compile(r"\bwhat quantity of\s+([a-z0-9_]+)\s+do i own\b"),
    re.compile(r"\bquantity of\s+([a-z0-9_]+)\s+do i own\b"),
    re.compile(r"\bhow many\s+([a-z0-9_]+)\s+do i own\b"),
    re.compile(r"\bhow many\s+([a-z0-9_]+)\s+i own\b"),
)

_RE_IN_SPLIT = re.compile(r",|\s+or\s+|\s+and\s+")


def detect_comparison_filters(lowered: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    symbolic = [
        (_RE_GTE, "_gte"),
        (_RE_LTE, "_lte"),
        (_RE_GT, "_gt"),
        (_RE_LT, "_lt"),
    ]
    for pattern, suffix in symbolic:
        for m in pattern.finditer(lowered):
            filters[f"{m.group(1)}{suffix}"] = m.group(2)

    lexical = [
        (_RE_GREATER_THAN, "_gt"),
        (_RE_LESS_THAN, "_lt"),
        (_RE_AFTER, "_gt"),
        (_RE_BEFORE, "_lt"),
    ]
    for pattern, suffix in lexical:
        for m in pattern.finditer(lowered):
            filters[f"{m.group(1)}{suffix}"] = m.group(2)

    return filters


def detect_negation_filters(lowered: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for m in _RE_NEGATION.finditer(lowered):
        filters[f"{m.group(1)}_ne"] = m.group(2)
    return filters


def detect_between_filters(lowered: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for m in _RE_BETWEEN_DATES.finditer(lowered):
        field = m.group(1)
        filters[f"{field}_gte"] = m.group(2)
        filters[f"{field}_lte"] = m.group(3)
    for m in _RE_BETWEEN.finditer(lowered):
        field = m.group(1)
        if f"{field}_gte" not in filters:
            filters[f"{field}_gte"] = m.group(2)
            filters[f"{field}_lte"] = m.group(3)
    return filters


def detect_in_filters(lowered: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for m in _RE_IN.finditer(lowered):
        field = m.group(1)
        values = [t.strip() for t in _RE_IN_SPLIT.split(m.group(2)) if t.strip()]
        if values:
            filters[f"{field}_in"] = values
    return filters


def detect_date_range_filters(lowered: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for m in _RE_DATE_RANGE.finditer(lowered):
        field = m.group(1)
        filters[f"{field}_gte"] = m.group(2)
        filters[f"{field}_lte"] = m.group(3)
    return filters


def detect_owned_asset(lowered: str) -> str | None:
    for pattern in _RE_OWNED_ASSET_PATTERNS:
        match = pattern.search(lowered)
        if match is not None:
            return match.group(1)
    return None
