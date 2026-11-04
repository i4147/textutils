from __future__ import annotations

from dataclasses import dataclass, field

from . import rows as R


@dataclass
class Region:
    kind: str
    start: int
    end: int
    pairs: dict[str, str] = field(default_factory=dict)
    text: str = ""


def find_regions(grid: list[list[str]], labels: list[str]) -> list[Region]:
    regions: list[Region] = []
    i, n = 0, len(labels)
    last_table_end = max(
        (idx for idx, lab in enumerate(labels) if lab in (R.HEADER, R.DATA)),
        default=-1,
    )
    while i < n:
        lab = labels[i]
        if lab == R.BLANK:
            i += 1
            continue
        if lab == R.HEADER or lab == R.DATA:
            j = _table_end(labels, i, grid)
            regions.append(Region("table", i, j))
            i = j + 1
            continue
        kind = lab
        j = i
        while j + 1 < n and labels[j + 1] in (kind, R.BLANK):
            if labels[j + 1] == kind:
                j += 1
            elif any(labels[k] == kind for k in range(j + 2, min(j + 3, n))):
                j += 1
            else:
                break
        if kind == R.METADATA and not _extract_pairs(grid, i, j):
            kind = R.PROSE
        region = Region(kind, i, j)
        if kind == R.METADATA:
            region.pairs = _extract_pairs(grid, i, j)
        else:
            region.text = " ".join(c for k in range(i, j + 1) for c in grid[k] if c)
        if kind == R.PROSE and last_table_end != -1 and i > last_table_end:
            region.kind = "footnotes"
        regions.append(region)
        i = j + 1
    return _merge_adjacent_footnotes(regions)


def _table_end(labels: list[str], start: int, grid: list[list[str]]) -> int:
    n = len(labels)
    j = start
    seen_data = False
    while j + 1 <= n - 1:
        nxt = labels[j + 1]
        if nxt == R.DATA:
            seen_data = True
            j += 1
        elif nxt == R.HEADER:
            if seen_data:
                break
            j += 1
        elif (
            nxt == R.PROSE
            and seen_data
            and j + 2 < n
            and labels[j + 2] == R.DATA
            and _is_sparse_continuation(grid[j + 1])
        ):
            j += 1
        elif nxt == R.BLANK:
            k = j + 1
            while k < n and labels[k] == R.BLANK:
                k += 1
            if k < n and labels[k] == R.DATA and (k - j) <= 2:
                j = k
            else:
                break
        else:
            break
    return j


_PAIR_LOOKAHEAD = 3


def _is_sparse_continuation(row: list[str]) -> bool:
    nonempty = [c for c in row if c]
    return 0 < len(nonempty) <= 3 and max(len(c) for c in nonempty) < 60


def _extract_pairs(grid: list[list[str]], start: int, end: int) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for r in range(start, end + 1):
        row = grid[r]
        for c, cell in enumerate(row):
            if not cell.endswith(":"):
                continue
            for v in range(c + 1, min(c + 1 + _PAIR_LOOKAHEAD, len(row))):
                if row[v]:
                    if not row[v].endswith(":"):
                        pairs[cell.rstrip(":").strip()] = row[v]
                    break
    return pairs


def _merge_adjacent_footnotes(regions: list[Region]) -> list[Region]:
    out: list[Region] = []
    for reg in regions:
        if out and reg.kind == "footnotes" and out[-1].kind == "footnotes":
            out[-1].end = reg.end
            out[-1].text = (out[-1].text + " " + reg.text).strip()
        else:
            out.append(reg)
    return out
