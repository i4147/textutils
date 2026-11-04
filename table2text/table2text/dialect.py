from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_SNIFF_BYTES = 64 * 1024
_DELIMITERS = [",", ";", "\t", "|"]
_QUOTES = ['"', "'"]
_UNCLOSED = -1


@dataclass
class Dialect:
    encoding: str
    delimiter: str
    quotechar: str


def sniff(path: str | Path) -> Dialect:
    with open(path, "rb") as f:
        raw = f.read(_SNIFF_BYTES)
        lookahead = f.read(1)
    encoding = _sniff_encoding(raw)
    sample = raw.decode(encoding, errors="replace")
    after = lookahead.decode(encoding, errors="replace")
    delimiter, quotechar = _sniff_delimiter(sample, after)
    return Dialect(encoding=encoding, delimiter=delimiter, quotechar=quotechar)


def _sniff_encoding(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def _sniff_delimiter(sample: str, after: str = "") -> tuple[str, str]:
    try:
        d = csv.Sniffer().sniff(sample, delimiters="".join(_DELIMITERS))
        delimiter, sniffed = d.delimiter, d.quotechar or '"'
    except csv.Error:
        counts = {delim: sum(1 for line in sample.splitlines() if delim in line) for delim in _DELIMITERS}
        best = max(counts, key=lambda k: counts[k])
        delimiter, sniffed = (best if counts[best] > 0 else ","), '"'
    return delimiter, _corroborate_quotechar(sample, delimiter, sniffed, after)


def _corroborate_quotechar(sample: str, delimiter: str, sniffed: str, after: str) -> str:
    counts = _count_quoted_fields(sample, delimiter, dict.fromkeys([*_QUOTES, sniffed]), after)
    best = max(counts.values())
    if best == 0:
        return '"'
    winners = [q for q, n in counts.items() if n == best]
    return '"' if '"' in winners else winners[0]


def _count_quoted_fields(sample: str, delimiter: str, candidates: dict[str, None], after: str) -> dict[str, int]:
    terminators = (delimiter, "\r", "\n")
    counts = dict.fromkeys(candidates, 0)
    i, n = 0, len(sample)
    at_field_start = True
    while i < n:
        c = sample[i]
        if at_field_start and c in counts:
            end = _closing_quote(sample, i, c, terminators, after)
            if end == _UNCLOSED and after:
                break
            if end is not None and end != _UNCLOSED:
                counts[c] += 1
                i, at_field_start = end + 1, False
                continue
        at_field_start = c in terminators
        i += 1
    return counts


def _closing_quote(sample: str, start: int, quote: str, terminators: tuple[str, ...], after: str) -> int | None:
    n = len(sample)
    j = start + 1
    while j < n:
        if sample[j] != quote:
            j += 1
            continue
        nxt = sample[j + 1] if j + 1 < n else after
        if nxt == quote:
            j += 2
            continue
        break
    if j >= n:
        return _UNCLOSED
    nxt = sample[j + 1] if j + 1 < n else after
    if nxt == "":
        return j
    return j if nxt in terminators else None


def load_grid(path: str | Path, dialect: Dialect | None = None) -> tuple[list[list[str]], Dialect]:
    dialect = dialect or sniff(path)
    with open(path, newline="", encoding=dialect.encoding) as f:
        reader = csv.reader(f, delimiter=dialect.delimiter, quotechar=dialect.quotechar)
        rows = [[cell.strip() for cell in row] for row in reader]
    width = max((len(r) for r in rows), default=0)
    for r in rows:
        r.extend([""] * (width - len(r)))
    return rows, dialect
