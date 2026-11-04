from __future__ import annotations

import re
from dataclasses import dataclass

BLANK = "blank"
BANNER = "banner"
METADATA = "metadata"
PROSE = "prose"
HEADER = "header"
DATA = "data"

_NUM_RE = re.compile(r"^-?(\d+|\d{1,3}(,\d{3})+)(\.\d*)?([eE]-?\d+)?%?$")
_LOOSE_NUM_RE = re.compile(r"^-?[\d.,]+([eE]-?\d+)?%?$")


def is_strict_number(cell: str) -> bool:
    return bool(_NUM_RE.match(cell))


_YEAR_RE = re.compile(r"^(19|20)\d\d$")
_ZEROPAD_RE = re.compile(r"^0\d+$")
_PROSE_MIN_LEN = 60


def _is_year_header(row: list[str], feats: RowFeatures) -> bool:
    years = [int(c) for c in row if _YEAR_RE.match(c)]
    if len(years) < 2 or len(years) != feats.n_num:
        return False
    ascending = all(b - a > 0 for a, b in zip(years, years[1:]))
    descending = all(b - a < 0 for a, b in zip(years, years[1:]))
    return ascending or descending


def _is_code_header(row: list[str], feats: RowFeatures) -> bool:
    codes = [c for c in row if _ZEROPAD_RE.match(c)]
    return (
        len(codes) >= 2
        and len(codes) == feats.n_num
        and len(set(codes)) == len(codes)
        and feats.n_nonempty > feats.n_num
    )


def _is_numeric_name_header(row: list[str], feats: RowFeatures) -> bool:
    return _is_year_header(row, feats) or _is_code_header(row, feats)


def cell_kind(cell: str) -> str:
    if cell == "":
        return "empty"
    if _LOOSE_NUM_RE.match(cell):
        return "num"
    return "str"


@dataclass
class RowFeatures:
    n_cells: int
    n_nonempty: int
    n_num: int
    max_len: int
    signature: tuple[str, ...]

    @property
    def num_ratio(self) -> float:
        return self.n_num / self.n_nonempty if self.n_nonempty else 0.0


def featurize(row: list[str]) -> RowFeatures:
    sig = tuple(cell_kind(c) for c in row)
    nonempty = [c for c in row if c != ""]
    return RowFeatures(
        n_cells=len(row),
        n_nonempty=len(nonempty),
        n_num=sum(1 for k in sig if k == "num"),
        max_len=max((len(c) for c in nonempty), default=0),
        signature=sig,
    )


def _is_metadata(row: list[str], feats: RowFeatures) -> bool:
    keys = sum(1 for c in row if c.endswith(":"))
    return keys >= 1 and feats.n_nonempty >= 2 and feats.n_nonempty <= 8


def _data_score(feats: RowFeatures, body_sig: tuple[str, ...] | None) -> bool:
    if feats.n_nonempty < 2:
        return False
    if feats.num_ratio >= 0.5:
        return True
    if body_sig is not None:
        for c, k in enumerate(body_sig):
            if k == "num" and c < len(feats.signature) and feats.signature[c] == "str":
                return False
        num_on_num = sum(1 for a, b in zip(feats.signature, body_sig) if b == "num" and a == "num")
        if num_on_num >= 2:
            return True
        agree = sum(1 for a, b in zip(feats.signature, body_sig) if b != "empty" and a == b)
        body_width = sum(1 for b in body_sig if b != "empty")
        return body_width >= 2 and agree / body_width >= 0.6
    return False


def _is_header(
    row: list[str],
    feats: RowFeatures,
    next_data: RowFeatures | None,
    name_header: bool = False,
) -> bool:
    if feats.n_nonempty < 2:
        return False
    if not name_header and feats.num_ratio > 0.34:
        return False
    if next_data is None:
        return False
    over = sum(1 for h, d in zip(feats.signature, next_data.signature) if h != "empty" and d != "empty")
    return over >= 2


def _matches_body(feats: RowFeatures, body: RowFeatures) -> bool:
    if not any(k == "num" for k in body.signature):
        return False
    return _data_score(feats, body.signature)


def _prev_significant(labels: list[str], i: int) -> int | None:
    for j in range(i - 1, -1, -1):
        if labels[j] != BLANK:
            return j
    return None


def _header_block_closed(labels: list[str], i: int) -> bool:
    seen_data = False
    for j in range(i - 1, -1, -1):
        if labels[j] == HEADER:
            return seen_data
        if labels[j] in (BLANK, PROSE, METADATA, BANNER):
            return False
        if labels[j] == DATA:
            seen_data = True
    return False


def _is_first_data_row(labels: list[str], i: int) -> bool:
    prev = _prev_significant(labels, i)
    if prev is None or labels[prev] != HEADER:
        return False
    above = _prev_significant(labels, prev)
    return above is None or labels[above] != HEADER


def _header_above(labels: list[str], i: int) -> int | None:
    for j in range(i - 1, -1, -1):
        if labels[j] == HEADER:
            return j
        if labels[j] in (BLANK, PROSE, METADATA, BANNER):
            return None
    return None


def _mark_headers(
    grid: list[list[str]],
    feats: list[RowFeatures],
    labels: list[str],
    name_hdr: list[bool],
) -> None:
    for i, f in enumerate(feats):
        if labels[i] != "?":
            continue
        if i + 1 < len(labels) and labels[i + 1] == BLANK:
            continue
        if _header_block_closed(labels, i):
            hdr = _header_above(labels, i)
            if hdr is not None and grid[i] == grid[hdr]:
                labels[i] = HEADER
            continue
        nxt = _next_significant(labels, i)
        if nxt is not None and labels[nxt] == DATA and _is_header(grid[i], f, feats[nxt], name_hdr[i]):
            if not name_hdr[i] and _is_first_data_row(labels, i) and _matches_body(f, feats[nxt]):
                labels[i] = DATA
            else:
                labels[i] = HEADER


def classify(grid: list[list[str]]) -> list[str]:
    feats = [featurize(r) for r in grid]
    name_hdr = [_is_numeric_name_header(r, f) for r, f in zip(grid, feats)]

    labels: list[str] = []
    for row, f in zip(grid, feats):
        if f.n_nonempty == 0:
            labels.append(BLANK)
        elif _is_metadata(row, f):
            labels.append(METADATA)
        elif f.n_nonempty == 1 and f.max_len >= _PROSE_MIN_LEN:
            labels.append(PROSE)
        else:
            labels.append("?")

    for i, f in enumerate(feats):
        if labels[i] == "?" and f.num_ratio >= 0.5 and f.n_nonempty >= 2:
            if name_hdr[i]:
                continue
            labels[i] = DATA

    def _eligible(i: int) -> bool:
        return (
            i < len(feats)
            and not name_hdr[i]
            and labels[i] in ("?", DATA)
            and feats[i].n_nonempty >= 2
            and feats[i].max_len < _PROSE_MIN_LEN
        )

    run_start = None
    for i in range(len(feats) + 1):
        in_run = _eligible(i) and (run_start is None or feats[i].signature == feats[run_start].signature)
        if in_run:
            if run_start is None:
                run_start = i
            continue
        if run_start is not None and i - run_start >= 3:
            for j in range(run_start, i):
                labels[j] = DATA
        run_start = i if _eligible(i) else None

    def _coherent(col_kind: dict[int, str], sig: tuple[str, ...]) -> bool:
        return all(col_kind.get(c, k) == k for c, k in enumerate(sig) if k != "empty")

    run_start = None
    col_kind: dict[int, str] = {}
    for i in range(len(feats) + 1):
        if _eligible(i) and (run_start is None or _coherent(col_kind, feats[i].signature)):
            if run_start is None:
                run_start = i
            for c, k in enumerate(feats[i].signature):
                if k != "empty":
                    col_kind[c] = k
            continue
        if run_start is not None and i - run_start >= 3 and any(k == "num" for k in col_kind.values()):
            for j in range(run_start, i):
                labels[j] = DATA
        if _eligible(i):
            run_start = i
            col_kind = {c: k for c, k in enumerate(feats[i].signature) if k != "empty"}
        else:
            run_start, col_kind = None, {}

    _mark_headers(grid, feats, labels, name_hdr)

    for i, f in enumerate(feats):
        if labels[i] == "?" and name_hdr[i] and f.num_ratio >= 0.5:
            labels[i] = DATA

    body_sig = None
    for i, f in enumerate(feats):
        if labels[i] == DATA:
            body_sig = f.signature
        elif labels[i] == "?" and _data_score(f, body_sig):
            labels[i] = DATA

    body_sig = None
    for i in range(len(feats) - 1, -1, -1):
        if labels[i] == DATA:
            body_sig = feats[i].signature
        elif labels[i] == "?" and _data_score(feats[i], body_sig):
            labels[i] = DATA

    _mark_headers(grid, feats, labels, name_hdr)

    in_leading = True
    for i, f in enumerate(feats):
        if labels[i] == "?":
            if in_leading and f.n_nonempty == 1:
                labels[i] = BANNER
            else:
                labels[i] = PROSE
                in_leading = False
        elif labels[i] != BLANK:
            in_leading = False
    return labels


def _next_significant(labels: list[str], i: int) -> int | None:
    for j in range(i + 1, len(labels)):
        if labels[j] not in (BLANK,):
            return j if labels[j] != "?" else _guess_forward(labels, j)
    return None


def _guess_forward(labels: list[str], j: int) -> int | None:
    for k in range(j, len(labels)):
        if labels[k] not in (BLANK, "?"):
            return k
    return None
