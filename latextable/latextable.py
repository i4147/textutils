import texttable


def draw_latex(
    table,
    caption=None,
    caption_short=None,
    caption_above=False,
    label=None,
    drop_columns=None,
    drop_rows=None,
    position=None,
    use_booktabs=False,
    multicolumn_header=None,
    alias=None,
):
    if type(table) != texttable.Texttable:
        rows = table
        table = texttable.Texttable()
        table.add_rows(rows)

    _sanitise_drop_columns(table._header, drop_columns, multicolumn_header)
    _sanitise_drop_rows(len(table._rows), drop_rows)

    if alias is not None:
        for s_src, s_dst in alias.items():
            table._header = [h.replace(s_src, s_dst) for h in table._header]
            for r_idx, row in enumerate(table._rows):
                table._rows[r_idx] = [r.replace(s_src, s_dst) for r in table._rows[r_idx]]

    out = ""
    out += _draw_latex_preamble(
        table=table,
        position=position,
        caption=caption if caption_above else None,
        caption_short=caption_short if caption_above else None,
        use_booktabs=use_booktabs,
    )
    out += _draw_latex_header(
        table=table, drop_columns=drop_columns, use_booktabs=use_booktabs, multicolumn_header=multicolumn_header
    )
    out += _draw_latex_content(table=table, drop_columns=drop_columns, drop_rows=drop_rows, use_booktabs=use_booktabs)
    out += _draw_latex_postamble(
        table=table,
        caption=caption if not caption_above else None,
        caption_short=caption_short if not caption_above else None,
        label=label,
        use_booktabs=use_booktabs,
    )
    return out


class DropColumnError(Exception):
    def __init__(self, column, header):
        super().__init__("Cannot drop column {:s} - column not in table header ({:s})\n".format(column, str(header)))


class MulticolumnHeaderError(Exception):
    def __init__(self, n_expected_columns, sum_multicolumn):
        super().__init__(
            "Mismatch between multicolumn size and number of actual columns. Got {:d} but expected {:d}.\n".format(
                sum_multicolumn, n_expected_columns
            )
        )


class DropRowError(Exception):
    def __init__(self, n_rows, row_idx):
        super().__init__("Cannot drop row {:d} - row is outside the range [1,{:d}]\n".format(row_idx, n_rows))


def _draw_latex_preamble(table, position, caption, caption_short, use_booktabs):
    out = "\\begin{table}"
    if position is not None:
        out += "[{}]".format(position)
    out += "\n"

    out += _draw_table_caption(caption, caption_short)

    out += _indent_text("\\begin{center}\n", 1)

    if not hasattr(table, "_align"):
        table._align = ["l"] * table._row_size
    if table._has_vlines() and not use_booktabs:
        column_str = "|".join(table._align)
    else:
        column_str = "".join(table._align)

    if table._has_border() and not use_booktabs:
        tabular_str = "\\begin{tabular}{|" + column_str + "|}\n"
    else:
        tabular_str = "\\begin{tabular}{" + column_str + "}\n"
    out += _indent_text(tabular_str, 2)

    return out


def _draw_latex_header(table, drop_columns, use_booktabs, multicolumn_header):
    out = ""
    if table._has_border() or use_booktabs:
        rule = "toprule" if use_booktabs else "hline"
        out += _indent_text("\\{}\n".format(rule), 3)

    header = _drop_columns(table._header.copy(), table._header, drop_columns)

    if multicolumn_header is not None:
        multicolumn_header_str = [
            f"\\multicolumn{{{count}}}{'{|c|}' if idx == 0 else '{c|}'}{{{name}}}"
            for idx, (name, count) in enumerate(multicolumn_header)
        ]
        out += _indent_text(" & ".join(multicolumn_header_str) + " \\\\\n", 3)
        out += _indent_text("\\{}\n".format(rule), 3)

    out += _indent_text(" & ".join(header) + " \\\\\n", 3)

    if table._has_header() or use_booktabs:
        rule = "midrule" if use_booktabs else "hline"
        out += _indent_text("\\{}\n".format(rule), 3)
    return out


def _draw_latex_content(table, drop_columns, drop_rows, use_booktabs):
    out = ""
    rows = _drop_rows(table._rows, drop_rows)
    for idx, row in enumerate(rows):
        row = _drop_columns(row, table._header, drop_columns)
        clean_row = _clean_row(row)
        out += _indent_text(" & ".join(clean_row) + " \\\\\n", 3)
        if table._has_hlines() and idx != len(table._rows) - 1 and not use_booktabs:
            out += _indent_text("\\hline\n", 3)
    return out


def _draw_latex_postamble(table, caption, caption_short, label, use_booktabs):
    out = ""
    if table._has_border() or use_booktabs:
        rule = "bottomrule" if use_booktabs else "hline"
        out += _indent_text("\\{}\n".format(rule), 3)

    out += _indent_text("\\end{tabular}\n", 2)
    out += _indent_text("\\end{center}\n", 1)

    out += _draw_table_caption(caption, caption_short)

    if label is not None:
        out += _indent_text("\\label{" + label + "}\n", 1)

    out += "\\end{table}"
    return out


def _draw_table_caption(caption, caption_short):
    out = ""
    if caption is not None:
        out += _indent_text("\\caption", 1)
        if caption_short is not None:
            out += "[" + caption_short + "]"
        out += "{" + caption + "}\n"
    return out


def _clean_row(row):
    clean_row = []
    for element in row:
        clean_row.append(element.replace("\n", ""))
    return clean_row


def _sanitise_drop_columns(header, drop_columns, multicolumn_header):
    if drop_columns is not None:
        for column in drop_columns:
            if column.upper() not in [h.upper() for h in header]:
                raise DropColumnError(column, header)
    if multicolumn_header is not None:
        n_expected_columns = len(header) if drop_columns is None else len(header) - len(drop_columns)
        sum_multicolumn = sum([h[1] for h in multicolumn_header])
        if n_expected_columns != sum_multicolumn:
            raise MulticolumnHeaderError(n_expected_columns, sum_multicolumn)


def _drop_columns(target, header, drop_columns):
    target = target[:]
    if drop_columns is None:
        return target
    to_delete = []
    for column in drop_columns:
        column_idx = header.index(column)
        to_delete.append(column_idx)
    for i in sorted(to_delete, reverse=True):
        del target[i]
    return target


def _sanitise_drop_rows(n_rows, drop_rows):
    if drop_rows is None:
        return
    for row_idx in drop_rows:
        if not 0 <= row_idx < n_rows:
            raise DropRowError(n_rows, row_idx)


def _drop_rows(rows, drop_rows):
    rows = rows[:]
    if drop_rows is None:
        return rows
    for i in sorted(drop_rows, reverse=True):
        del rows[i]
    return rows


def _indent_text(text, indent):
    return "\t" * indent + text
