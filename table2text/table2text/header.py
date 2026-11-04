from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import rows as R
from .regions import Region

_UNIT_RE = re.compile(r"^[^\s]{1,12}/[^\s]{1,14}$")

_UNIT_VOCAB = {
    "%",
    "kg",
    "g",
    "mg",
    "t",
    "tonne",
    "tonnes",
    "km",
    "m",
    "mm",
    "cm",
    "mi",
    "miles",
    "wh",
    "kwh",
    "mwh",
    "gwh",
    "twh",
    "gj",
    "mj",
    "kj",
    "litres",
    "liters",
    "litre",
    "liter",
    "l",
    "ml",
    "m2",
    "m3",
    "km2",
    "ha",
    "ft",
    "ft2",
    "ft3",
    "gal",
    "gallons",
    "hours",
    "hour",
    "hr",
    "hrs",
    "min",
    "mins",
    "s",
    "sec",
    "days",
    "weeks",
    "months",
    "years",
    "nights",
    "kgco2e",
    "tco2e",
    "co2e",
    "gbp",
    "usd",
    "eur",
    "pence",
    "therm",
    "therms",
    "toe",
    "ktoe",
    "mtoe",
    "btu",
    "mmbtu",
    "kcal",
    "cal",
    "kw",
    "mw",
    "gw",
    "bar",
    "psi",
    "tkm",
    "pkm",
    "vkm",
    "mpg",
    "mph",
    "kph",
    "units",
    "unit",
    "each",
    "items",
    "trips",
    "passengers",
    "lb",
    "lbs",
    "oz",
    "st",
    "nmi",
    "nm",
    "in",
    "yd",
    "yds",
    "inches",
    "ton",
    "tons",
}


def _is_unit_token(cell: str) -> bool:
    token = cell.replace("\n", " ").split("[")[0].strip()
    if _UNIT_RE.match(token):
        return True
    return token.lower().strip("()") in _UNIT_VOCAB


def _compose_flat_name(group: str, name: str, unit: str, index: int) -> str:
    if name:
        flat = f"{group} / {name}" if group else name
    else:
        flat = group or f"col_{index}"
    return f"{flat} [{unit}]" if unit else flat


def _dedupe(names: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for n in names:
        counts[n] = counts.get(n, 0) + 1
    seen: dict[str, int] = {}
    out = []
    for i, n in enumerate(names):
        if counts[n] > 1:
            seen[n] = seen.get(n, 0) + 1
            if seen[n] > 1:
                n = f"{n} (col {i})"
        out.append(n)
    return out


@dataclass
class ColumnNode:
    index: int
    name: str
    group: str = ""
    unit: str = ""
    flat_name: str = ""

    def __post_init__(self) -> None:
        if not self.flat_name:
            self.flat_name = _compose_flat_name(self.group, self.name, self.unit, self.index)


@dataclass
class HeaderInfo:
    header_rows: list[int]
    data_start: int
    columns: list[ColumnNode] = field(default_factory=list)

    @property
    def depth(self) -> int:
        return len(self.header_rows)

    @property
    def groups(self) -> list[str]:
        seen: list[str] = []
        for c in self.columns:
            if c.group and c.group not in seen:
                seen.append(c.group)
        return seen


def _is_units_row(cells: list[str]) -> bool:
    nonempty = [c for c in cells if c]
    if len(nonempty) < 2:
        return False
    hits = sum(1 for c in nonempty if _is_unit_token(c))
    return hits / len(nonempty) >= 0.5


def _table_width(grid: list[list[str]], region: Region) -> int:
    width = 0
    for r in range(region.start, region.end + 1):
        for c in range(len(grid[r]) - 1, -1, -1):
            if grid[r][c]:
                width = max(width, c + 1)
                break
    return width


def analyze_header(grid: list[list[str]], labels: list[str], region: Region) -> HeaderInfo:
    header_rows = []
    r = region.start
    while r <= region.end and labels[r] == R.HEADER:
        header_rows.append(r)
        r += 1
    data_start = r
    width = _table_width(grid, region)

    if not header_rows:
        cols = [ColumnNode(index=c, name=f"col_{c}") for c in range(width)]
        return HeaderInfo(header_rows=[], data_start=data_start, columns=cols)

    block = [grid[r][:width] for r in header_rows]

    units: list[str] = [""] * width
    if len(block) >= 2 and _is_units_row(block[-1]):
        units = [c.replace("\n", " ").strip() for c in block[-1]]
        block = block[:-1]

    name_row = block[-1]
    group_rows = block[:-1]

    filled_groups: list[list[str]] = []
    for grow in group_rows:
        filled, current = [], ""
        for cell in grow:
            if cell:
                current = cell
            filled.append(current)
        filled_groups.append(filled)

    names: list[str] = []
    groups: list[str] = []
    unit_vals: list[str] = []
    for c in range(width):
        name = name_row[c].replace("\n", " ").strip() if c < len(name_row) else ""
        group = " / ".join(filled[c] for filled in filled_groups if filled[c])
        names.append(name)
        groups.append(group)
        unit_vals.append(units[c].split("[")[0].strip() if units[c] else "")

    flat_names = _dedupe([_compose_flat_name(groups[c], names[c], unit_vals[c], c) for c in range(width)])
    columns = [
        ColumnNode(
            index=c,
            name=names[c],
            group=groups[c],
            unit=unit_vals[c],
            flat_name=flat_names[c],
        )
        for c in range(width)
    ]
    return HeaderInfo(header_rows=header_rows, data_start=data_start, columns=columns)
