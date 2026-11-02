import copy
import shutil
from typing import List, Dict, Optional, Union
from textframe.characters.corners import top_left, top_right, bottom_left, bottom_right
from textframe.helpers.calcs.calc_column_widths import calc_column_widths
from textframe.helpers.checkers.is_last_element import is_last_element
from textframe.helpers.formatters.string.row_frame_divider import row_frame_divider
from textframe.helpers.formatters.string.row_outer_border import row_outer_border
from textframe.helpers.renderers.string.render_grid_frame_string import render_single_line_grid, render_multi_line_grid
from textframe.helpers.renderers.string.render_table_frame_string import render_table_frame_string
from textframe.helpers.renderers.string.render_text_frame_string import render_text_frame_string
from textframe.typing import (
    BaseBorder,
    TableInputColumnDict,
    HeaderAlignment,
    RowColumnDivider,
    HeaderColumnDivider,
    TextAlignment,
    GridInputColumnDict,
)


class TextFrame:
    def __init__(
        self,
        border: BaseBorder = "thick",
        frame_width: int = None,
        left_padding: int = 1,
        frame_divider: BaseBorder = "thick",
        html_block_size: int = 6,
        html_character_size: int = 12,
    ):
        self._border = border if border != "none" else "blank"
        self._frame_width = (
            frame_width
            if frame_width
            else shutil.get_terminal_size((120 + (left_padding * 2), 0))[0] - (left_padding * 2)
        )
        self._left_padding = left_padding
        self._frame_divider = frame_divider
        self._output_frame_list = []

    def add_text_frame(
        self,
        text: Union[str, int, float],
        multiline: bool = True,
        max_lines: Optional[int] = None,
        text_align: TextAlignment = "left",
        text_padding: int = 1,
        frame_base_divider: BaseBorder = "thick",
        trunc_value: str = "...",
    ):
        max_lines = 1 if not multiline else max_lines
        self._output_frame_list.append({
            "type": "text",
            "column_list": [{"width": self._frame_width - 2, "divider": "blank"}],
            "string": text,
            "base_divider": frame_base_divider,
            "max_lines": max_lines,
            "align": text_align,
            "padding": text_padding,
            "trunc_value": trunc_value,
        })

    def add_grid_frame(
        self,
        columns: List[Union[str, GridInputColumnDict]],
        column_padding: int = 1,
        column_divider: RowColumnDivider = "thin",
        frame_base_divider: BaseBorder = "thick",
        multiline: bool = True,
        max_lines: int = None,
        trunc_value: str = "...",
    ):
        max_lines = 1 if not multiline else max_lines
        columns = copy.deepcopy(columns)
        grid_column_list = []
        for grid_column_item in columns:
            if type(grid_column_item) == str:
                grid_column_list.append({
                    "divider": self._frame_divider,
                    "string": grid_column_item,
                    "align": "left",
                    "padding": column_padding,
                    "trunc_value": trunc_value,
                })
            elif type(grid_column_item) == dict:
                grid_column_item["string"] = grid_column_item["string"]
                grid_column_item["divider"] = (
                    column_divider if "divider" not in grid_column_item else grid_column_item["divider"]
                )
                grid_column_item["align"] = grid_column_item["align"] if "align" in grid_column_item else "left"
                grid_column_item["padding"] = column_padding
                grid_column_item["trunc_value"] = trunc_value
                if "width" in grid_column_item:
                    grid_column_item["width"] = grid_column_item["width"]
                grid_column_list.append(grid_column_item)
        grid_column_list = calc_column_widths(
            columns=grid_column_list, frame_width=self._frame_width, column_padding=column_padding
        )
        self._output_frame_list.append({
            "type": "grid",
            "column_list": grid_column_list,
            "base_divider": frame_base_divider,
            "max_lines": max_lines,
        })

    def add_table_frame(
        self,
        columns: List[TableInputColumnDict],
        rows: List[Dict[str, Union[str, int, float]]],
        column_padding: int = 1,
        row_line_divider: BaseBorder = "thin",
        row_column_divider: RowColumnDivider = "thin",
        frame_base_divider: BaseBorder = "thick",
        header_align: HeaderAlignment = "column",
        header_column_divider: HeaderColumnDivider = "rows",
        header_base_divider: BaseBorder = "thick",
        hide_header: bool = False,
    ):
        columns = copy.deepcopy(columns)
        rows = copy.deepcopy(rows)
        columns = calc_column_widths(columns=columns, frame_width=self._frame_width, column_padding=column_padding)
        header_column_list = []
        row_column_list = []
        for column_index, column_item in enumerate(columns):
            column_align_out = column_item["align"] if "align" in column_item else "left"
            header_align_out = header_align if header_align != "column" else column_align_out
            column_divider_out = column_item["divider"] if "divider" in column_item else row_column_divider
            header_divider_out = header_column_divider if header_column_divider != "rows" else column_divider_out
            header_column_list.append({
                "width": column_item["width"],
                "divider": header_divider_out,
                "string": column_item["key"],
                "align": header_align_out,
                "padding": column_padding,
                "trunc_value": ".",
            })
            row_column_list.append({
                "width": column_item["width"],
                "divider": column_divider_out,
                "key": column_item["key"],
                "align": column_align_out,
                "padding": column_padding,
                "trunc_value": "...",
            })
        if not hide_header:
            self._output_frame_list.append({
                "type": "grid",
                "column_list": header_column_list,
                "base_divider": header_base_divider,
                "max_lines": 1,
            })
        self._output_frame_list.append({
            "type": "table",
            "column_list": row_column_list,
            "table_row_list": rows,
            "row_line_divider": row_line_divider,
            "base_divider": frame_base_divider,
        })

    def to_string(self):
        return_string = ""
        if len(self._output_frame_list) > 0:
            top_border_inner = row_frame_divider(
                divider=self._border, column_list_top=[], column_list_bottom=self._output_frame_list[0]["column_list"]
            )
            return_string += (
                f"{' ' * self._left_padding}{top_left[self._border]}{top_border_inner}{top_right[self._border]}\n"
            )
            for frame_index, frame_item in enumerate(self._output_frame_list):
                if frame_item["type"] == "text":
                    return_string += render_text_frame_string(
                        text_frame_dict=frame_item, frame_border=self._border, left_padding=self._left_padding
                    )
                if frame_item["type"] == "grid":
                    if frame_item["max_lines"] == 1:
                        return_string += render_single_line_grid(
                            column_list=frame_item, frame_border=self._border, left_padding=self._left_padding
                        )
                    else:
                        return_string += render_multi_line_grid(
                            column_list=frame_item, frame_border=self._border, left_padding=self._left_padding
                        )
                if frame_item["type"] == "table":
                    return_string += render_table_frame_string(
                        table_dict=frame_item, frame_border=self._border, left_padding=self._left_padding
                    )
                if not is_last_element(frame_index, self._output_frame_list):
                    if self._output_frame_list[frame_index]["base_divider"] != "none":
                        frame_divider_inner = row_frame_divider(
                            divider=self._output_frame_list[frame_index]["base_divider"],
                            column_list_top=self._output_frame_list[frame_index]["column_list"],
                            column_list_bottom=self._output_frame_list[frame_index + 1]["column_list"],
                        )
                        frame_divider_outer = row_outer_border(
                            row_string=frame_divider_inner,
                            outer_border=self._border,
                            row_divider=self._output_frame_list[frame_index]["base_divider"],
                        )
                        return_string += f"{' ' * self._left_padding}{frame_divider_outer}\n"
            bottom_border_inner = row_frame_divider(
                divider=self._border, column_list_top=self._output_frame_list[-1]["column_list"], column_list_bottom=[]
            )
            return_string += f"{' ' * self._left_padding}{bottom_left[self._border]}{bottom_border_inner}{bottom_right[self._border]}\n"
        return return_string

    def print(self):
        print(self.to_string())

    def __repr__(self):
        return self.to_string()

    def to_html(self):
        pass

    def _repr_html_(self):
        return self.to_html()
