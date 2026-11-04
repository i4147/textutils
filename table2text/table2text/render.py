from __future__ import annotations

import os
from dataclasses import dataclass

from .ast import FileAST, TableNode
from .columns import ColumnStats
from .rank import (
    EMPTY_PADDING,
    SPANNING_GROUPS,
    KEY_META,
    MULTI_ROW_HEADER,
    ColumnRun,
    Quirk,
    collapse_runs,
    column_tier,
    group_expand_order,
    group_runs,
    HIGH,
    file_verdict,
    header_uncertain,
    quirks,
)

_GIST = 70
_ENUM_VALUES = 6
_ENUM_CHARS = 60
_SAMPLE_CHARS = 110


@dataclass(frozen=True)
class Detail:
    map_mode: str = "full"
    meta_mode: str = "all"
    prose_mode: str = "gist"
    table_mode: str = "full"
    col_mode: str = "full"
    samples: int = 3
    col_expand: int = -1
    quirk_mode: str = "full"
    recipe_mode: str = "full"


@dataclass
class Brief:
    text: str
    facts: frozenset


class _Emit:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self._facts: set[tuple] = set()

    def line(self, text: str = "") -> None:
        self.lines.append(text)

    def fact(self, *parts) -> None:
        self._facts.add(tuple(parts))

    def build(self) -> Brief:
        return Brief(text="\n".join(self.lines), facts=frozenset(self._facts))


def _trunc(s: str, n: int) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _pct(x: float) -> str:
    return f"{round(x * 100)}%"


def _num(x: float) -> str:
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return f"{x:.6g}"


def render_column_full(c: ColumnStats) -> str:
    bits = [c.type]
    if c.null_ratio > 0:
        bits.append(f"{_pct(c.null_ratio)} null")
    if c.is_enum:
        vals = c.distinct[:_ENUM_VALUES]
        joined = _trunc(" | ".join(vals), _ENUM_CHARS)
        more = "" if len(c.distinct) <= _ENUM_VALUES else ", …"
        bits.append(f"enum{{{joined}{more}}}")
    elif c.min is not None:
        bits.append(f"range {_num(c.min)}..{_num(c.max)}")
    elif c.type == "str":
        n = len(c.distinct)
        bits.append(f"{n}+ distinct" if c.distinct_overflow else f"{n} distinct")
    if c.is_ffill_key:
        bits.append("ffill key")
    return f"  [{c.node.index}] {c.node.flat_name}: " + ", ".join(bits)


def render_column_compact(c: ColumnStats) -> str:
    return f"  [{c.node.index}] {c.node.flat_name}: {c.type}"


def _span(run: ColumnRun) -> str:
    return f"{run.start}" if run.start == run.end else f"{run.start}-{run.end}"


def render_run(run: ColumnRun) -> str:
    n = len(run.columns)
    label = f"  [{_span(run)}] {n} col{'s' if n > 1 else ''}, {run.type}"
    if run.group:
        label += f', group "{_trunc(run.group, 40)}"'
    return label


def _emit_columns(e: _Emit, ti: int, table: TableNode, mode: str, expand: int = -1) -> None:
    cols = table.stats.columns
    if mode == "full" or mode == "compact":
        render = render_column_full if mode == "full" else render_column_compact
        for c in cols:
            e.line(render(c))
            e.fact("col", ti, c.node.index)
            e.fact("col_name", ti, c.node.index, c.node.flat_name)
            e.fact("col_type", ti, c.node.index, c.type)
            if mode == "full":
                e.fact("col_stat", ti, c.node.index)
        return

    if mode == "packed":
        _emit_packed(e, ti, table, expand)
        return

    runs = collapse_runs(cols, by_group=(mode == "runs"), protect_keys=(mode == "runs"))
    for run in runs:
        collapse = mode == "floor" or run.is_run
        if collapse:
            e.line(render_run(run))
        for c in run.columns:
            e.fact("col", ti, c.node.index)
            e.fact("col_type", ti, c.node.index, c.type)
            if not collapse:
                e.line(render_column_compact(c))
                e.fact("col_name", ti, c.node.index, c.node.flat_name)


_PACK_WIDTH = 220


def _emit_packed(e: _Emit, ti: int, table: TableNode, expand: int) -> None:
    groups = group_runs(table.stats.columns)
    order = group_expand_order(groups)
    quota = len(groups) if expand < 0 else expand
    expanded = set(order[:quota])
    for gi, run in enumerate(groups):
        first, last = run.columns[0].node.index, run.columns[-1].node.index
        for c in run.columns:
            e.fact("col", ti, c.node.index)
            e.fact("col_type", ti, c.node.index, c.type)
        if run.protected:
            for c in run.columns:
                e.line(render_column_compact(c))
                e.fact("col_name", ti, c.node.index, c.node.flat_name)
            continue
        label = run.group or run.type
        if gi not in expanded:
            span = f"{first}" if first == last else f"{first}-{last}"
            n = len(run.columns)
            e.line(f"  [{span}] {_trunc(label, 80)} — {n} col{'s' if n > 1 else ''}, {run.type}")
            continue
        entries = []
        prefix = (run.group + " / ") if run.group else ""
        for c in run.columns:
            leaf = c.node.flat_name
            if prefix and leaf.startswith(prefix):
                leaf = leaf[len(prefix) :]
            entries.append(f"[{c.node.index}] {_trunc(leaf, 70)}")
            e.fact("col_name", ti, c.node.index, c.node.flat_name)
        line = f"  [{first}-{last}] {_trunc(label, 80)}: "
        for entry in entries:
            joined = entry if line.endswith(": ") else f"{line}; {entry}"
            if line.endswith(": "):
                joined = f"{line}{entry}"
            if len(joined) > _PACK_WIDTH and not line.endswith(": "):
                e.line(line)
                line = f"   {entry}"
            else:
                line = joined
        if line.strip():
            e.line(line)


def _column_summary(table: TableNode) -> str:
    runs = collapse_runs(table.stats.columns, by_group=False, by_nulls=False)
    return "; ".join(f"[{_span(r)}] {len(r.columns)} {r.type}" for r in runs)


def _header_phrase(table: TableNode, short: bool) -> str:
    h = table.header
    if not h.header_rows:
        return "no header" if short else "no header row detected"
    span = f"{h.header_rows[0]}" if h.depth == 1 else f"{h.header_rows[0]}-{h.header_rows[-1]}"
    if short:
        phrase = f"hdr {span} d{h.depth}"
        if h.groups:
            phrase += f"/{len(h.groups)}g"
        return phrase + ("(low-conf)" if header_uncertain(table) else "")
    phrase = f"header row{'s' if h.depth > 1 else ''} {span} (depth {h.depth}"
    if h.groups:
        phrase += f", {len(h.groups)} group spans"
    if header_uncertain(table):
        phrase += ", low confidence"
    return phrase + ")"


def _span_rows(table: TableNode) -> int:
    return table.region.end - table.header.data_start + 1


def _table_headline(ti: int, table: TableNode, short: bool) -> str:
    name = f"T{ti + 1}"
    r = table.region
    n_cols = len(table.stats.columns)
    n_rows = table.stats.n_data_rows
    if short:
        return f"{name} {r.start}-{r.end} {_header_phrase(table, True)} {n_rows}r x {n_cols}c: {_column_summary(table)}"
    line = (
        f"{name}  rows {r.start}-{r.end}  {_header_phrase(table, False)}  "
        f"{n_rows} data row{'s' if n_rows != 1 else ''} x {n_cols} cols"
    )
    gap = _span_rows(table) - n_rows
    if gap > 0:
        line += f" (+{gap} non-data rows inside the span)"
    return line


def _emit_samples(e: _Emit, ti: int, table: TableNode, n: int) -> None:
    for k, row in enumerate(table.stats.sample_rows[:n]):
        e.line("  sample: " + _trunc(" | ".join(row), _SAMPLE_CHARS))
        e.fact("sample", ti, k)


def _emit_tables(e: _Emit, ast: FileAST, d: Detail) -> None:
    if not ast.tables:
        return
    e.line("TABLES:")
    for ti, t in enumerate(ast.tables):
        short = d.table_mode == "floor"
        e.line(_table_headline(ti, t, short))
        e.fact("table", ti, t.region.start, t.region.end)
        e.fact("header", ti, t.header.depth)
        if short:
            for c in t.stats.columns:
                e.fact("col", ti, c.node.index)
                e.fact("col_type", ti, c.node.index, c.type)
            continue
        _emit_columns(e, ti, t, d.col_mode, d.col_expand)
        _emit_samples(e, ti, t, d.samples)


def _meta_pairs(pairs: dict[str, str], mode: str) -> list[tuple[str, str]]:
    items = list(pairs.items())
    if mode == "keys":
        items = [kv for kv in items if kv[0].lower() in KEY_META]
    return items


def _table_index(ast: FileAST, region) -> int | None:
    for ti, t in enumerate(ast.tables):
        if t.region is region:
            return ti
    return None


def _emit_map(e: _Emit, ast: FileAST, d: Detail) -> None:
    if d.map_mode == "floor":
        parts = []
        for r in ast.regions:
            e.fact("region", r.kind, r.start, r.end)
            ti = _table_index(ast, r)
            if ti is not None:
                parts.append(f"T{ti + 1} {r.start}-{r.end}")
            else:
                parts.append(f"{r.start}-{r.end} {r.kind}")
        e.line("MAP: " + " | ".join(parts))
        return

    e.line("MAP:")
    for r in ast.regions:
        e.fact("region", r.kind, r.start, r.end)
        span = f"rows {r.start}-{r.end}"
        ti = _table_index(ast, r)
        if ti is not None:
            e.line(f"  {span}  table T{ti + 1}")
            continue
        if r.kind == "metadata":
            items = _meta_pairs(r.pairs, d.meta_mode)
            if d.meta_mode == "count" or not items:
                e.line(f"  {span}  metadata, {len(r.pairs)} pairs")
            else:
                for k, _ in items:
                    e.fact("meta", k)
                rendered = "; ".join(f"{k}={v}" for k, v in items)
                e.line(f"  {span}  metadata  {_trunc(rendered, 160)}")
            continue
        if d.prose_mode == "gist" and d.map_mode == "full" and r.text:
            e.fact("gist", r.start, r.end)
            e.line(f'  {span}  {r.kind}  "{_trunc(r.text, _GIST)}"  (skip)')
        else:
            e.line(f"  {span}  {r.kind}  (skip)")


def _table_list(indices: list[int]) -> str:
    parts, i = [], 0
    while i < len(indices):
        j = i
        while j + 1 < len(indices) and indices[j + 1] == indices[j] + 1:
            j += 1
        if j - i >= 1:
            parts.append(f"T{indices[i] + 1}-T{indices[j] + 1}")
        else:
            parts.append(f"T{indices[i] + 1}")
        i = j + 1
    return ", ".join(parts)


def _emit_quirks(e: _Emit, ast: FileAST, d: Detail) -> None:
    qs = quirks(ast)
    for q in qs:
        e.fact("quirk", q.table, q.type)
    if not qs:
        return
    e.line("QUIRKS:")
    if d.quirk_mode == "full":
        for q in qs:
            who = "FILE" if q.table < 0 else f"T{q.table + 1}"
            if d.col_mode == "packed" and q.type == SPANNING_GROUPS:
                e.line(f"  {who}: {len(q.payload)} spanning column groups — see the column index above")
                continue
            e.line(f"  {who}: {q.sentence()}")
        return

    by_type: dict[str, list[Quirk]] = {}
    for q in qs:
        by_type.setdefault(q.type, []).append(q)
    for qtype, group in by_type.items():
        if group[0].table < 0:
            e.line(f"  {group[0].sentence()}")
            continue
        who = _table_list([q.table for q in group])
        if qtype == EMPTY_PADDING:
            e.line(
                f"  {who}: cols beyond each table's own column count are empty "
                f"padding (file is {ast.n_cols} wide): trim after load"
            )
        elif qtype == MULTI_ROW_HEADER:
            e.line(f"  {who}: multi-row header (row span on each TABLES line): flatten the column index after load")
        else:
            buckets: dict[tuple[str, ...], list[int]] = {}
            for q in group:
                buckets.setdefault(q.payload, []).append(q.table)
            for payload, tables in buckets.items():
                sentence = Quirk(qtype, tables[0], payload).sentence()
                e.line(f"  {_table_list(tables)}: {_trunc(sentence, 160)}")


def _header_arg(t: TableNode) -> str:
    if not t.header.header_rows:
        return "None"
    if t.header.depth == 1:
        return "0"
    return str(list(range(t.header.depth)))


def _ffill_cols(t: TableNode) -> list[int]:
    return [c.node.index for c in t.stats.columns if c.is_ffill_key]


@dataclass(frozen=True)
class RecipeSpec:
    skip: int
    nrows: int
    header_arg: str
    header_depth: int
    ncols: int
    has_padding: bool
    ffill: tuple[int, ...]


def _recipe_spec(t: TableNode) -> RecipeSpec:
    skip = t.header.header_rows[0] if t.header.header_rows else t.header.data_start
    return RecipeSpec(
        skip=skip,
        nrows=_span_rows(t),
        header_arg=_header_arg(t),
        header_depth=t.header.depth,
        ncols=len(t.stats.columns),
        has_padding=t.stats.empty_padding_start is not None,
        ffill=tuple(_ffill_cols(t)),
    )


def _read_args(spec: RecipeSpec) -> str:
    args = f"nrows={spec.nrows}, header={spec.header_arg}"
    if spec.skip:
        args = f"skiprows={spec.skip}, " + args
    return args


def _slice_suffix(spec: RecipeSpec) -> str:
    if not spec.has_padding:
        return ""
    return f".iloc[:, :{spec.ncols}]"


_PANDAS_DEFAULTS = {"sep": ",", "encoding": "utf-8", "quotechar": '"'}


def _dialect_kwargs(ast: FileAST) -> str:
    found = {
        "sep": ast.dialect.delimiter,
        "encoding": ast.dialect.encoding,
        "quotechar": ast.dialect.quotechar,
    }
    diff = [f"{k}={v!r}" for k, v in found.items() if v != _PANDAS_DEFAULTS[k]]
    return ", ".join(diff)


def _emit_recipe_facts(e: _Emit, specs: list[RecipeSpec]) -> None:
    for ti, spec in enumerate(specs):
        e.fact("recipe_skiprows", ti, spec.skip)
        e.fact("recipe_nrows", ti, spec.nrows)
        e.fact("recipe_header", ti, spec.header_arg)
        if spec.has_padding:
            e.fact("recipe_trim", ti, spec.ncols)
        if spec.header_depth >= 2:
            e.fact("recipe_flatten", ti)
        if spec.ffill:
            e.fact("recipe_ffill", ti, spec.ffill)


def _emit_recipe(e: _Emit, ast: FileAST, d: Detail) -> None:
    if not ast.tables:
        return
    specs = [_recipe_spec(t) for t in ast.tables]
    _emit_recipe_facts(e, specs)
    name = os.path.basename(ast.path)
    e.line("RECIPE:")
    e.line("```python")
    e.line("import pandas as pd")
    e.line(f"p = {name!r}")
    if ast.input_kind == "xlsx":
        e.fact("sheet", ast.sheet)
        read = f"pd.read_excel(p, sheet_name={ast.sheet!r}, "
    else:
        dialect = _dialect_kwargs(ast)
        read = "pd.read_csv(p, "
        if dialect:
            e.line(f"dial = dict({dialect})")
            e.fact("dialect", dialect)
            read = "pd.read_csv(p, **dial, "

    if d.recipe_mode == "floor":
        tuples = []
        for ti, spec in enumerate(specs):
            e.fact("recipe", ti)
            tuples.append(f"({spec.skip},{spec.nrows},{spec.header_depth},{spec.ncols})")
        e.line("# (skiprows, nrows, header_depth, ncols) — one tuple per table")
        e.line(f"specs = [{', '.join(tuples)}]")
        e.line(f"dfs = [{read}skiprows=s, nrows=n,")
        e.line("       header=list(range(h)) if h else None).iloc[:, :c]")
        e.line("       for s, n, h, c in specs]")
        e.line("# then flatten multi-row headers and ffill, per QUIRKS")
        e.line("```")
        return

    multi = any(spec.header_depth >= 2 for spec in specs)
    if multi:
        e.line("def flat(df):")
        e.line("    group = [''] * (df.columns.nlevels - 1)")
        e.line("    names, seen = [], {}")
        e.line("    for i, levels in enumerate(df.columns):")
        e.line("        for j, v in enumerate(levels[:-1]):")
        e.line("            if 'Unnamed' not in str(v):")
        e.line("                group[j] = str(v)")
        e.line("        leaf = str(levels[-1])")
        e.line("        gpath = ' / '.join(p for p in group if p)")
        e.line("        if 'Unnamed' in leaf:")
        e.line("            n = gpath or f'col_{i}'")
        e.line("        else:")
        e.line("            n = f'{gpath} / {leaf}' if gpath else leaf")
        e.line("        seen[n] = seen.get(n, 0) + 1")
        e.line("        names.append(f'{n} (col {i})' if seen[n] > 1 else n)")
        e.line("    return names")
    for ti, (t, spec) in enumerate(zip(ast.tables, specs)):
        e.fact("recipe", ti)
        var = f"t{ti + 1}"
        e.line(f"# T{ti + 1}: rows {t.region.start}-{t.region.end}")
        gap = spec.nrows - t.stats.n_data_rows
        if gap > 0:
            e.line(f"# {gap} of these {spec.nrows} rows are not data rows")
        e.line(f"{var} = {read}{_read_args(spec)}){_slice_suffix(spec)}")
        if d.recipe_mode == "compact":
            continue
        if spec.header_depth >= 2:
            e.line(f"{var}.columns = flat({var})")
        if spec.ffill:
            idx = f"{var}.iloc[:, {list(spec.ffill)}]"
            e.line(f"{idx} = {idx}.ffill()")
    if d.recipe_mode == "compact":
        e.line("# then: tN.columns = flat(tN) where the header is multi-row,")
        e.line("# and ffill the column positions listed in QUIRKS")
    e.line("```")


def render(ast: FileAST, detail: Detail) -> Brief:
    e = _Emit()
    name = os.path.basename(ast.path)
    e.fact("file", ast.n_rows, ast.n_cols)
    if ast.input_kind == "xlsx":
        source = f"xlsx, sheet {ast.sheet!r}"
    else:
        source = f"{ast.dialect.encoding}, delimiter '{ast.dialect.delimiter}'"
    e.line(f"FILE: {name} — {ast.n_rows} rows x {ast.n_cols} cols, {source}")
    e.line(f"VERDICT: {file_verdict(ast)}")
    _emit_map(e, ast, detail)
    _emit_tables(e, ast, detail)
    _emit_quirks(e, ast, detail)
    _emit_recipe(e, ast, detail)
    return e.build()
