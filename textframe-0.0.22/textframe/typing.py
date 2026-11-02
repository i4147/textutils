from typing import Dict, List, Literal, Optional, TypedDict, Union

TextAlignment = Literal["left", "center", "right"]
HeaderAlignment = Literal["column", "center"]
BaseBorder = Literal["none", "blank", "thin", "thick", "double"]
HeaderColumnDivider = Literal["rows", "blank", "thin", "thick", "double"]
RowColumnDivider = Literal["blank", "thin", "thick", "double"]


class TextBoxColumnDict(TypedDict):
    width: int | str
    divider: RowColumnDivider


class TextFrameDict(TypedDict):
    type: Literal["string"]
    column_list: list[TextBoxColumnDict]
    string: str
    base_divider: BaseBorder
    max_lines: Optional[int]
    align: TextAlignment
    padding: int
    trunc_value: str


class GridColumnFrameDict(TypedDict):
    width: int | str
    divider: RowColumnDivider
    string: str
    align: TextAlignment
    padding: int
    trunc_value: str


class GridFrameDict(TypedDict):
    type: Literal["grid"]
    column_list: list[GridColumnFrameDict]
    base_divider: BaseBorder
    max_lines: Optional[int]


class TableColumnFrameDict(TypedDict):
    width: int | str
    divider: RowColumnDivider
    key: str
    align: TextAlignment
    padding: int
    trunc_value: str


class TableRowsFrameDict(TypedDict):
    type: Literal["table"]
    column_list: list[TableColumnFrameDict]
    table_row_list: list[dict[str, str | int | float]]
    row_line_divider: BaseBorder
    base_divider: BaseBorder


class MinGridInputColumnDict(TypedDict):
    string: str | int | float


class GridInputColumnDict(MinGridInputColumnDict, total=False):
    width: int | str
    align: TextAlignment
    divider: RowColumnDivider


class MinTableInputColumnDict(TypedDict):
    key: str


class TableInputColumnDict(MinTableInputColumnDict, total=False):
    width: int | str
    align: TextAlignment
    divider: RowColumnDivider
