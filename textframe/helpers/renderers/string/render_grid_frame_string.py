from typing import TYPE_CHECKING
from textframe.characters.line_v import v_line
from textframe.helpers.checkers.is_last_element import is_last_element
from textframe.helpers.formatters.string.cell_string import cell_string_multi_line, cell_string_single_line
from textframe.helpers.formatters.string.row_outer_border import row_outer_border

if TYPE_CHECKING:
    from textframe.typing import BaseBorder, GridFrameDict


def render_single_line_grid(column_list: GridFrameDict, frame_border: BaseBorder, left_padding: int):
    grid_line_string = ""
    for column_index, column_item in enumerate(column_list["column_list"]):
        grid_line_string += cell_string_single_line(
            string=column_item["string"],
            width=column_item["width"],
            padding=column_item["padding"],
            align=column_item["align"],
            trunc_value=column_item["trunc_value"],
        )
        if not is_last_element(column_index, column_list["column_list"]):
            grid_line_string += v_line[column_item["divider"]]
    grid_line_inner = row_outer_border(row_string=grid_line_string, outer_border=frame_border)
    return_string = f"{' ' * left_padding}{grid_line_inner}\n"
    return return_string


def render_multi_line_grid(column_list: GridFrameDict, frame_border: BaseBorder, left_padding: int):
    max_lines = column_list["max_lines"] or 0
    return_columns_array = []
    for column_item in column_list["column_list"]:
        column_string_array = cell_string_multi_line(
            string=column_item["string"],
            width=column_item["width"],
            padding=column_item["padding"],
            align=column_item["align"],
            trunc_value=column_item["trunc_value"],
            max_lines=max_lines,
        )
        max_lines = max(max_lines, len(column_string_array))
        return_columns_array.append(column_string_array)
    grid_frame_string = ""
    for grid_line_index in range(max_lines):
        grid_line_string = ""
        for column_index, column_item in enumerate(column_list["column_list"]):
            if grid_line_index < len(return_columns_array[column_index]):
                grid_line_string += return_columns_array[column_index][grid_line_index]
            else:
                grid_line_string += cell_string_single_line(
                    string="",
                    width=column_item["width"],
                    padding=column_item["padding"],
                    align=column_item["align"],
                    trunc_value=column_item["trunc_value"],
                )
            if not is_last_element(column_index, column_list["column_list"]):
                grid_line_string += v_line[column_item["divider"]]
        grid_line_inner = row_outer_border(row_string=grid_line_string, outer_border=frame_border)
        grid_frame_string += f"{' ' * left_padding}{grid_line_inner}\n"
    return grid_frame_string
