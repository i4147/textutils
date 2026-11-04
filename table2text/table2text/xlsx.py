from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .dialect import Dialect

_WORKBOOK = "xl/workbook.xml"
_WORKBOOK_RELS = "xl/_rels/workbook.xml.rels"
_SHARED = "xl/sharedStrings.xml"
_COL_LETTERS = re.compile(r"[A-Z]+")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _col_index(ref: str) -> int:
    letters = _COL_LETTERS.match(ref).group()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def _dim_shape(ref: str) -> tuple[int, int]:
    end = ref.split(":")[-1]
    m = re.match(r"([A-Z]+)(\d+)", end)
    if not m:
        return 0, 0
    return int(m.group(2)), _col_index(end) + 1


def _workbook_rels(zf: zipfile.ZipFile) -> dict[str, str]:
    root = ET.fromstring(zf.read(_WORKBOOK_RELS))
    out = {}
    for rel in root:
        target = rel.get("Target", "")
        target = target[1:] if target.startswith("/") else "xl/" + target
        out[rel.get("Id")] = target
    return out


def _sheets(zf: zipfile.ZipFile) -> list[tuple[str, str, str]]:
    rels = _workbook_rels(zf)
    root = ET.fromstring(zf.read(_WORKBOOK))
    sheets = []
    for el in root.iter():
        if _local(el.tag) != "sheet":
            continue
        name = el.get("name", "")
        state = el.get("state", "visible")
        rid = next((v for k, v in el.attrib.items() if _local(k) == "id"), None)
        sheets.append((name, state, rels.get(rid, "")))
    return sheets


def _resolve_sheet(sheets: list[tuple[str, str, str]], sheet: str | None) -> tuple[str, str]:
    if not sheets:
        raise ValueError("workbook has no sheets")
    if sheet is None:
        for name, state, part in sheets:
            if state == "visible":
                return name, part
        return sheets[0][0], sheets[0][2]
    if sheet.isdigit():
        i = int(sheet)
        if not 0 <= i < len(sheets):
            raise ValueError(f"--sheet {i} out of range (workbook has {len(sheets)} sheets)")
        return sheets[i][0], sheets[i][2]
    for name, state, part in sheets:
        if name == sheet:
            return name, part
    names = ", ".join(repr(n) for n, _, _ in sheets)
    raise ValueError(f"no sheet named {sheet!r}; sheets are: {names}")


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if _SHARED not in zf.namelist():
        return []
    strings: list[str] = []
    parts: list[str] | None = None
    with zf.open(_SHARED) as f:
        for event, el in ET.iterparse(f, events=("start", "end")):
            tag = _local(el.tag)
            if event == "start":
                if tag == "si":
                    parts = []
            elif tag == "t":
                if parts is not None:
                    parts.append(el.text or "")
            elif tag == "si":
                strings.append("".join(parts or ()))
                parts = None
                el.clear()
    return strings


def _fmt_number(v: str) -> str:
    try:
        f = float(v)
    except ValueError:
        return v
    if f.is_integer() and abs(f) < 1e16:
        return str(int(f))
    return repr(f)


def _cell_value(c: ET.Element, shared: list[str]) -> str:
    t = c.get("t")
    if t == "inlineStr":
        return "".join(x.text or "" for x in c.iter() if _local(x.tag) == "t")
    v = next((ch.text for ch in c if _local(ch.tag) == "v"), None)
    if v is None:
        return ""
    if t == "s":
        return shared[int(v)]
    if t == "str":
        return v
    if t == "b":
        return "TRUE" if v == "1" else "FALSE"
    if t == "e":
        return v
    return _fmt_number(v)


def _read_sheet(zf: zipfile.ZipFile, part: str, shared: list[str]) -> list[list[str]]:
    grid: list[list[str]] = []
    max_col = 0
    dim_rows = dim_cols = 0
    cells: dict[int, str] | None = None
    row_num = 0
    next_row = 1
    with zf.open(part) as f:
        for event, el in ET.iterparse(f, events=("start", "end")):
            tag = _local(el.tag)
            if event == "start":
                if tag == "row":
                    cells = {}
                    r = el.get("r")
                    row_num = int(r) if r else next_row
                continue
            if tag == "c":
                ref = el.get("r")
                col = _col_index(ref) if ref else (max(cells) + 1 if cells else 0)
                cells[col] = _cell_value(el, shared)
                el.clear()
            elif tag == "row":
                while len(grid) < row_num - 1:
                    grid.append([])
                width = max(cells) + 1 if cells else 0
                max_col = max(max_col, width)
                row = [""] * width
                for col, val in cells.items():
                    row[col] = val
                grid.append(row)
                next_row = row_num + 1
                cells = None
                el.clear()
            elif tag == "dimension":
                dim_rows, dim_cols = _dim_shape(el.get("ref", ""))
                el.clear()

    height = max(len(grid), dim_rows)
    width = max(max_col, dim_cols)
    while len(grid) < height:
        grid.append([])
    for row in grid:
        if len(row) < width:
            row.extend([""] * (width - len(row)))
    return grid


def load_xlsx(path: str | Path, sheet: str | None = None) -> tuple[list[list[str]], Dialect, str]:
    with zipfile.ZipFile(path) as zf:
        sheets = _sheets(zf)
        name, part = _resolve_sheet(sheets, sheet)
        shared = _shared_strings(zf)
        grid = _read_sheet(zf, part, shared)
    grid = [[cell.strip() for cell in row] for row in grid]
    return grid, Dialect(encoding="xlsx", delimiter="", quotechar='"'), name
