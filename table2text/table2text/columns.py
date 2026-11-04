from __future__ import annotations

from dataclasses import dataclass, field

from .header import ColumnNode, HeaderInfo
from .rows import cell_kind, is_strict_number

_DISTINCT_CAP = 24
_ENUM_MAX = 12
_SAMPLE_ROWS = 3
_SAMPLE_CELL_LEN = 80


@dataclass
class ColumnStats:
    node: ColumnNode
    type: str = "empty"
    n_values: int = 0
    n_rows: int = 0
    null_ratio: float = 1.0
    distinct: list[str] = field(default_factory=list)
    distinct_overflow: bool = False
    min: float | None = None
    max: float | None = None
    is_ffill_key: bool = False

    @property
    def is_enum(self) -> bool:
        return self.type == "str" and not self.distinct_overflow and 0 < len(self.distinct) <= _ENUM_MAX


@dataclass
class TableStats:
    columns: list[ColumnStats]
    n_data_rows: int
    sample_rows: list[list[str]]
    empty_padding_start: int | None = None


def _num(cell: str) -> float | None:
    if not is_strict_number(cell):
        return None
    try:
        return float(cell.replace(",", "").rstrip("%"))
    except ValueError:
        return None


def analyze_columns(
    grid: list[list[str]],
    data_rows: list[int],
    header: HeaderInfo,
    full_width: int,
) -> TableStats:
    cols = [ColumnStats(node=n) for n in header.columns]
    n_rows = len(data_rows)

    for ci, cs in enumerate(cols):
        kinds: set[str] = set()
        prev_nonempty = False
        block_starts = 0
        saw_float = False
        first_value_row: int | None = None
        for r in data_rows:
            cell = grid[r][ci]
            if cell == "":
                prev_nonempty = False
                continue
            cs.n_values += 1
            if first_value_row is None:
                first_value_row = r
            if not prev_nonempty:
                block_starts += 1
            prev_nonempty = True
            k = cell_kind(cell)
            kinds.add(k)
            if k == "num":
                if "." in cell or "e" in cell.lower():
                    saw_float = True
                v = _num(cell)
                if v is None:
                    kinds.add("str")
                else:
                    cs.min = v if cs.min is None else min(cs.min, v)
                    cs.max = v if cs.max is None else max(cs.max, v)
            if not cs.distinct_overflow:
                if cell not in cs.distinct:
                    if len(cs.distinct) < _DISTINCT_CAP:
                        cs.distinct.append(cell)
                    else:
                        cs.distinct_overflow = True

        cs.n_rows = n_rows
        cs.null_ratio = 1 - (cs.n_values / n_rows) if n_rows else 1.0
        if not kinds:
            cs.type = "empty"
        elif kinds == {"num"}:
            cs.type = "float" if saw_float else "int"
        elif kinds == {"str"}:
            cs.type = "str"
        else:
            cs.type = "mixed"

        spans_from_top = cs.n_values == 1 and data_rows and first_value_row == data_rows[0]
        cs.is_ffill_key = (
            cs.type == "str"
            and 0.2 <= cs.null_ratio
            and block_starts == cs.n_values
            and (block_starts >= 2 or spans_from_top)
            and not cs.distinct_overflow
        )

    empty_padding_start = None
    if full_width > len(cols):
        empty_padding_start = len(cols)

    samples = []
    for r in data_rows[:_SAMPLE_ROWS]:
        samples.append([c[:_SAMPLE_CELL_LEN] for c in grid[r][: len(cols)]])

    return TableStats(
        columns=cols,
        n_data_rows=n_rows,
        sample_rows=samples,
        empty_padding_start=empty_padding_start,
    )
