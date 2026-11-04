from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import rows as R
from .columns import TableStats, analyze_columns
from .dialect import Dialect, load_grid
from .header import HeaderInfo, analyze_header
from .regions import Region, find_regions
from .xlsx import load_xlsx

_GIST_LEN = 100


@dataclass
class TableNode:
    region: Region
    header: HeaderInfo
    stats: TableStats
    quirks: list[str] = field(default_factory=list)


@dataclass
class FileAST:
    path: str
    n_rows: int
    n_cols: int
    dialect: Dialect
    regions: list[Region]
    tables: list[TableNode]
    input_kind: str = "csv"
    sheet: str | None = None

    def to_dict(self) -> dict:
        d = {
            "path": self.path,
            "shape": [self.n_rows, self.n_cols],
            "dialect": {
                "encoding": self.dialect.encoding,
                "delimiter": self.dialect.delimiter,
                "quotechar": self.dialect.quotechar,
            },
            "regions": [_region_dict(r) for r in self.regions],
            "tables": [_table_dict(t) for t in self.tables],
        }
        if self.input_kind != "csv":
            d["input_kind"] = self.input_kind
            d["sheet"] = self.sheet
        return d

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), **kwargs)


def _region_dict(r: Region) -> dict:
    d: dict = {"kind": r.kind, "rows": [r.start, r.end]}
    if r.kind == "metadata":
        d["pairs"] = r.pairs
    elif r.kind != "table":
        d["gist"] = r.text[:_GIST_LEN]
    return d


def _table_dict(t: TableNode) -> dict:
    return {
        "rows": [t.region.start, t.region.end],
        "header_rows": t.header.header_rows,
        "header_depth": t.header.depth,
        "groups": t.header.groups,
        "n_data_rows": t.stats.n_data_rows,
        "empty_padding_start": t.stats.empty_padding_start,
        "columns": [
            {
                "index": c.node.index,
                "name": c.node.name,
                "group": c.node.group,
                "unit": c.node.unit,
                "flat_name": c.node.flat_name,
                "type": c.type,
                "n_values": c.n_values,
                "null_ratio": round(c.null_ratio, 3),
                "n_distinct": len(c.distinct),
                "distinct_is_lower_bound": c.distinct_overflow,
                "enum": c.distinct if c.is_enum else None,
                "range": [c.min, c.max] if c.min is not None else None,
                "ffill": c.is_ffill_key,
            }
            for c in t.stats.columns
        ],
        "sample_rows": t.stats.sample_rows,
        "quirks": t.quirks,
    }


def _quirks(t: TableNode, n_cols: int) -> list[str]:
    q = []
    if t.header.depth >= 2:
        q.append(f"multi-row header (rows {t.header.header_rows[0]}-{t.header.header_rows[-1]}): flatten before use")
    if t.header.groups:
        q.append(f"spanning column groups: {', '.join(t.header.groups[:8])}")
    ffill = [c.node.flat_name for c in t.stats.columns if c.is_ffill_key]
    if ffill:
        q.append(f"forward-fill columns before use: {', '.join(ffill)}")
    units = [c for c in t.stats.columns if c.node.unit]
    if units:
        q.append("units row merged into column names")
    if t.stats.empty_padding_start is not None:
        q.append(f"cols {t.stats.empty_padding_start}+ are empty padding (file is {n_cols} wide)")
    if not t.header.header_rows:
        q.append("no header row detected; positional column names")
    return q


def parse(path: str | Path, sheet: str | None = None) -> FileAST:
    if Path(path).suffix.lower() in (".xlsx", ".xlsm"):
        grid, dialect, sheet_name = load_xlsx(path, sheet)
        input_kind = "xlsx"
    else:
        grid, dialect = load_grid(path)
        input_kind, sheet_name = "csv", None
    labels = R.classify(grid)
    regions = find_regions(grid, labels)

    tables = []
    for reg in regions:
        if reg.kind != "table":
            continue
        header = analyze_header(grid, labels, reg)
        data_rows = [r for r in range(reg.start, reg.end + 1) if labels[r] == R.DATA]
        stats = analyze_columns(grid, data_rows, header, len(grid[0]) if grid else 0)
        node = TableNode(region=reg, header=header, stats=stats)
        node.quirks = _quirks(node, len(grid[0]) if grid else 0)
        tables.append(node)

    return FileAST(
        path=str(path),
        n_rows=len(grid),
        n_cols=len(grid[0]) if grid else 0,
        dialect=dialect,
        regions=regions,
        tables=tables,
        input_kind=input_kind,
        sheet=sheet_name,
    )
