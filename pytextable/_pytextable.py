import functools
import typing

RowT = typing.Sequence[typing.Any]
DataT = typing.Sequence[RowT]
HeaderT = typing.Sequence[str]
MidruleCallbackT = typing.Callable[[RowT, RowT], bool]


def _no_extra_midrule(_row: RowT, _last_row: RowT) -> bool:
    return False


def tostring(
    data: DataT,
    *,
    header: HeaderT = None,
    table: bool = True,
    centering: bool = True,
    caption: str = "",
    label: str = "",
    alignment: str = "",
    fmt: str = "",
    indentation: int = 4,
    booktabs: bool = True,
    midrule_condition: MidruleCallbackT = _no_extra_midrule,
) -> str:
    n_columns = _get_num_columns(data)
    content = _create_table_rows(
        data,
        header=header,
        fmt=fmt,
        booktabs=booktabs,
        midrule_condition=midrule_condition,
    )
    wrap = functools.partial(_wrap_tex_environment, indentation=indentation)
    content = wrap("tabular", content, cmd=_table_alignment(alignment, n_columns))
    if table:
        if label:
            content = f"\\label{{{label}}}\n{content}"
        if caption:
            content = f"\\caption{{{caption}}}\n{content}"
        if centering:
            content = f"\\centering\n{content}"
        content = wrap("table", content)
    return content


def write(
    data: DataT,
    outfile: str,
    *,
    writemode: str = "w",
    encoding: str = "utf-8",
    **kwargs: typing.Any,
) -> None:
    with open(outfile, writemode, encoding=encoding) as f:
        f.write(tostring(data, **kwargs))


def _get_num_columns(data: DataT) -> int:
    n_columns = sorted({len(row) for row in data})
    if len(n_columns) != 1:
        found = ", ".join(str(num) for num in n_columns)
        raise ValueError(f"All rows must have the same number of columns. Found: {found}.")
    return n_columns[0]


def _create_table_rows(
    data: DataT,
    *,
    header: HeaderT = None,
    fmt: str = "",
    booktabs: bool = True,
    midrule_condition: MidruleCallbackT = _no_extra_midrule,
) -> str:
    row_end = r" \\"

    def create_row(row: RowT, fmt: str = fmt) -> str:
        text = " & ".join(f"{elem:{fmt}}" for elem in row)
        return text + row_end

    headstr = create_row(header, fmt="") if header is not None else ""
    rows = []
    last_elem = data[0]
    for elem in data:
        row = create_row(elem)
        if midrule_condition(elem, last_elem):
            row = "\n\\midrule\n" + row
        rows.append(row)
        last_elem = elem
    rowstr = "\n".join(rows)
    if booktabs and headstr:
        return f"\\toprule\n{headstr}\n\\midrule\n{rowstr}\n\\bottomrule"
    if booktabs:
        return f"\\toprule\n{rowstr}\n\\bottomrule"
    if headstr:
        return f"{headstr} \\hline\n{rowstr}"
    return rowstr


def _wrap_tex_environment(
    environment: str,
    text: str,
    *,
    cmd: str = "",
    options: str = "",
    indentation: int = 4,
) -> str:
    options = f"[{options}]" if options else ""
    cmd = f"{{{cmd}}}" if cmd else ""
    begin = rf"\begin{{{environment}}}{cmd}{options}"
    inner_lines = [" " * indentation + line for line in text.split("\n") if line.strip()]
    content = "\n".join(inner_lines)
    end = rf"\end{{{environment}}}"
    return f"{begin}\n{content}\n{end}\n"


def _table_alignment(alignment: str, n_columns: int) -> str:
    if not alignment:
        return "c" * n_columns
    align_chars = "lcr|"
    if set(alignment) - set(align_chars):
        raise ValueError(f"Invalid alignment '{alignment}'. Must only contain: {align_chars}.")
    alignment_chars = alignment.replace("|", "")
    n_alignment_chars = len(alignment_chars)
    if n_alignment_chars == n_columns:
        return alignment
    if n_alignment_chars == 1:
        raw_alignment = alignment_chars * n_columns
        if len(alignment) == 1:
            return raw_alignment
        if len(alignment) == 2:
            return "|".join(raw_alignment)
        if len(alignment) == 3:
            return "|" + "|".join(raw_alignment) + "|"
        raise ValueError(f"Too many | separators passed to alignment '{alignment}'. Must pass exactly 1 or 2.")
    raise ValueError(
        f"Number of alignment characters ({n_alignment_chars}) must match number of columns {{n_columns}}."
    )
