from __future__ import annotations

from dataclasses import dataclass

from .ast import FileAST, TableNode
from .columns import ColumnStats

INFINITE = 0
HIGH = 1
MEDIUM = 2
LOW = 3
NEAR_ZERO = 4

KEY_META = ("scope", "year", "version", "factor set", "emissions source")

_MIN_RUN = 3


_KEY_CARDINALITY = 12
_MIN_KEY_ROWS = 3


def is_key_like(c: ColumnStats) -> bool:
    if c.is_ffill_key or c.is_enum:
        return True
    if not c.n_values:
        return False
    if (
        c.type in ("int", "float")
        and not c.distinct_overflow
        and len(c.distinct) <= _KEY_CARDINALITY
        and len(c.distinct) < c.n_values
    ):
        return True
    if c.type not in ("str", "int") or c.n_values < _MIN_KEY_ROWS:
        return False
    return c.distinct_overflow or len(c.distinct) == c.n_values


def column_tier(c: ColumnStats) -> int:
    if is_key_like(c):
        return HIGH
    if c.type in ("int", "float"):
        return LOW
    return MEDIUM


def region_tier(kind: str) -> int:
    if kind in ("table", "banner"):
        return INFINITE
    if kind == "metadata":
        return HIGH
    return MEDIUM


@dataclass
class ColumnRun:
    start: int
    end: int
    columns: list[ColumnStats]
    type: str
    group: str
    protected: bool = False

    @property
    def is_run(self) -> bool:
        return not self.protected and len(self.columns) >= _MIN_RUN

    @property
    def null_bucket(self) -> int:
        return null_bucket(self.columns[0])


def null_bucket(c: ColumnStats) -> int:
    if c.null_ratio <= 0.01:
        return 0
    return 1 if c.null_ratio < 0.5 else 2


def collapse_runs(
    columns: list[ColumnStats],
    by_group: bool = True,
    protect_keys: bool = False,
    by_nulls: bool = True,
) -> list[ColumnRun]:
    runs: list[ColumnRun] = []
    for c in columns:
        group = c.node.group if by_group else ""
        protected = protect_keys and column_tier(c) == HIGH
        if (
            runs
            and not protected
            and not runs[-1].protected
            and (not by_nulls or runs[-1].null_bucket == null_bucket(c))
            and runs[-1].type == c.type
            and runs[-1].group == group
            and runs[-1].end == c.node.index - 1
        ):
            runs[-1].end = c.node.index
            runs[-1].columns.append(c)
        else:
            runs.append(
                ColumnRun(
                    start=c.node.index,
                    end=c.node.index,
                    columns=[c],
                    type=c.type,
                    group=group,
                    protected=protected,
                )
            )
    return runs


def _top_group(c: ColumnStats) -> str:
    return (c.node.group or "").split(" / ")[0]


def group_runs(columns: list[ColumnStats]) -> list[ColumnRun]:
    runs: list[ColumnRun] = []
    for c in columns:
        top = _top_group(c)
        protected = column_tier(c) == HIGH
        if (
            runs
            and not protected
            and not runs[-1].protected
            and runs[-1].group == top
            and (top or runs[-1].type == c.type)
            and runs[-1].end == c.node.index - 1
        ):
            runs[-1].end = c.node.index
            runs[-1].columns.append(c)
            if runs[-1].type != c.type:
                runs[-1].type = "mixed"
        else:
            runs.append(
                ColumnRun(
                    start=c.node.index,
                    end=c.node.index,
                    columns=[c],
                    type=c.type,
                    group=top,
                    protected=protected,
                )
            )
    return runs


def group_expand_order(runs: list[ColumnRun]) -> list[int]:

    def cost(run: ColumnRun) -> int:
        return sum(len(c.node.flat_name) for c in run.columns)

    def key(gi: int):
        run = runs[gi]
        best = min((column_tier(c) for c in run.columns), default=LOW)
        return (best, cost(run), gi)

    return sorted((gi for gi, run in enumerate(runs) if not run.protected), key=key)


STACKED = "stacked-tables"
MULTI_ROW_HEADER = "multi-row-header"
SPANNING_GROUPS = "spanning-groups"
FFILL = "ffill"
UNITS_ROW = "units-row"
EMPTY_PADDING = "empty-padding"
NO_HEADER = "no-header"
UNCERTAIN_HEADER = "uncertain-header"


@dataclass
class Quirk:
    type: str
    table: int
    payload: tuple[str, ...] = ()

    def sentence(self) -> str:
        p = self.payload
        if self.type == STACKED:
            return f"{p[0]} stacked tables — read each by its own row offsets"
        if self.type == MULTI_ROW_HEADER:
            return f"header spans rows {p[0]}-{p[1]}: flatten the column index after load"
        if self.type == SPANNING_GROUPS:
            return f"spanning column groups: {', '.join(p)}"
        if self.type == FFILL:
            return f"forward-fill after load (labels written once per group): {', '.join(p)}"
        if self.type == UNITS_ROW:
            return "units live in the last header row, merged into column names"
        if self.type == EMPTY_PADDING:
            return f"cols {p[0]}+ are empty padding (file is {p[1]} wide): keep only cols 0-{int(p[0]) - 1} after load"
        if self.type == NO_HEADER:
            return "no header row detected: read with header=None, positional names"
        if self.type == UNCERTAIN_HEADER:
            return f"header depth {p[0]} is a low-confidence call — verify rows {p[1]}-{p[2]}"
        raise AssertionError(f"quirk type outside the closed vocabulary: {self.type}")


def header_uncertain(t: TableNode) -> bool:
    if t.header.depth < 2:
        return False
    explained = bool(t.header.groups) or any(c.node.unit for c in t.stats.columns)
    return not explained or t.stats.n_data_rows <= 3


def quirks(ast: FileAST) -> list[Quirk]:
    out: list[Quirk] = []
    if len(ast.tables) > 1:
        out.append(Quirk(STACKED, -1, (str(len(ast.tables)),)))
    for ti, t in enumerate(ast.tables):
        h, s = t.header, t.stats
        if h.depth >= 2:
            out.append(
                Quirk(
                    MULTI_ROW_HEADER,
                    ti,
                    (str(h.header_rows[0]), str(h.header_rows[-1])),
                )
            )
        if h.groups:
            out.append(Quirk(SPANNING_GROUPS, ti, tuple(h.groups)))
        ffill = tuple(f"[{c.node.index}] {c.node.flat_name}" for c in s.columns if c.is_ffill_key)
        if ffill:
            out.append(Quirk(FFILL, ti, ffill))
        if any(c.node.unit for c in s.columns):
            out.append(Quirk(UNITS_ROW, ti))
        if s.empty_padding_start is not None:
            out.append(Quirk(EMPTY_PADDING, ti, (str(s.empty_padding_start), str(ast.n_cols))))
        if not h.header_rows:
            out.append(Quirk(NO_HEADER, ti))
        if header_uncertain(t):
            out.append(
                Quirk(
                    UNCERTAIN_HEADER,
                    ti,
                    (str(h.depth), str(t.region.start), str(h.data_start)),
                )
            )
    return out


def file_verdict(ast: FileAST) -> str:
    n_tables = len(ast.tables)
    quirky = any(t.quirks for t in ast.tables)
    if n_tables == 1 and len(ast.regions) == 1 and not quirky:
        return "clean single table, header on row 1"
    if n_tables == 0:
        return "no tabular data found — text regions only"
    noun = "table" if n_tables == 1 else "stacked tables"
    return f"report sheet, not clean — {n_tables} {noun} inside"
