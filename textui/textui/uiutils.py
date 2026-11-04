from __future__ import print_function, absolute_import, division
import math

from .uierrors import UIErrorWrapper, UITermError

try:
    from shutil import get_terminal_size
except ImportError:
    from backports.shutil_get_terminal_size import get_terminal_size

_test_entries = [
    "Alpha",
    "Bravo",
    "Charlie",
    "Delta",
    "Echo",
    "Foxtrot",
    "Golf",
    "Hotel",
    "India",
    "Juliet",
    "Kilo",
    "Lima",
    "Mike",
    "November",
    "Oscar",
    "Papa",
    "Quebec",
    "Romeo",
    "Sierra",
    "Tango",
    "Unicorn",
    "Victor",
    "Whiskey",
    "X-ray",
    "Yankee",
    "Zulu",
]


def print_in_columns(entries, buffer_chars=4, fixed_width_columns=False, column_major=True):
    n_term_col = get_terminal_size().columns
    max_entry_length = _max_len(entries) + buffer_chars
    n_entry_col = n_term_col // max_entry_length

    def make_rows(n_columns, col_width):
        last_rows = None
        n_rows = int(math.ceil(len(entries) / n_columns))
        n_per_row = int(math.ceil(len(entries) / n_rows))
        while True:
            rows = []
            if not column_major:
                for i in range(0, len(entries), n_per_row):
                    j = min(i + n_per_row, len(entries))
                    sub_list = entries[i:j]
                    this_row = []
                    for c, val in enumerate(sub_list):
                        this_row.append(_pad_string(val, col_width))
                    rows.append(this_row)

            else:
                for r in range(0, n_rows):
                    sub_list = [entries[i_r] for i_r in range(r, len(entries), n_rows)]
                    this_row = [_pad_string(val, col_width) for c, val in enumerate(sub_list)]
                    rows.append(this_row)

            if fixed_width_columns:
                return rows

            rows = shrink_cols(rows)
            longest_row_length = _max_len(join_rows(rows))
            if longest_row_length > n_term_col:
                if last_rows is None:
                    UIErrorWrapper.raise_error(
                        UITermError("The initial column spacing resulted in a row wider than the terminal")
                    )
                else:
                    return last_rows
            else:
                last_rows = rows
                if column_major:
                    n_rows -= 1
                    if n_rows <= 0:
                        return rows
                else:
                    n_per_row += 1

    def rows_to_columns(rows):
        cols = []
        max_n_per_row = _max_len(rows)
        for i in range(max_n_per_row):
            this_col = [row[i] for row in rows if len(row) > i]
            cols.append(this_col)
        return cols

    def columns_to_rows(columns):
        rows = []
        n_rows = _max_len(columns)
        for r in range(n_rows):
            rows.append([col[r] for col in columns if len(col) > r])
        return rows

    def shrink_cols(rows):
        columns = rows_to_columns(rows)
        for col in columns:
            width = _max_len(col, prefxn=lambda x: x.rstrip()) + buffer_chars
            for i, val in enumerate(col):
                col[i] = _pad_string(val.rstrip(), width)
        return columns_to_rows(columns)

    def join_rows(rows):
        return ["".join(r) for r in rows]

    all_rows = make_rows(n_entry_col, max_entry_length)

    for row in join_rows(all_rows):
        print(row)


def _max_len(values, prefxn=lambda x: x):
    return max([len(prefxn(v)) for v in values])


def _pad_string(s, length):
    return s + " " * (length - len(s))
