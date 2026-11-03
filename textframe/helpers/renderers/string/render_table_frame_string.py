from typing import TYPE_CHECKING
from textframe.characters.line_v import v_line
from textframe.helpers.checkers.is_last_element import is_last_element
from textframe.helpers.formatters.string.cell_string import cell_string_single_line
from textframe.helpers.formatters.string.row_frame_divider import row_frame_divider
from textframe.helpers.formatters.string.row_outer_border import row_outer_border

if TYPE_CHECKING:
    from textframe.typing import BaseBorder, TableRowsFrameDict


def render_table_frame_string(table_dict: TableRowsFrameDict, frame_border: BaseBorder, left_padding) -> str:
    return_string = ""
    row_line_strings_list = []
    line_string = None
    if table_dict["row_line_divider"] != "none":
        line_string = row_frame_divider(
            divider=table_dict["row_line_divider"],
            column_list_top=table_dict["column_list"],
            column_list_bottom=table_dict["column_list"],
        )
    for row_index, row_item in enumerate(table_dict["table_row_list"]):
        row_line_string = ""
        for column_index, column_item in enumerate(table_dict["column_list"]):
            row_line_string += cell_string_single_line(
                string=row_item[column_item["key"]],
                width=column_item["width"],
                padding=column_item["padding"],
                align=column_item["align"],
                trunc_value=column_item["trunc_value"],
            )
            if not is_last_element(column_index, table_dict["column_list"]):
                row_line_string += v_line[column_item["divider"]]
        row_line_strings_list.append(row_outer_border(row_string=row_line_string, outer_border=frame_border))
        if not is_last_element(row_index, table_dict["table_row_list"]) and line_string:
            row_line_strings_list.append(
                row_outer_border(
                    row_string=line_string, outer_border=frame_border, row_divider=table_dict["row_line_divider"]
                )
            )
    if table_dict["row_line_divider"] == "blank":
        row_line_strings_list.insert(0, row_outer_border(row_string=line_string, outer_border=frame_border))
        row_line_strings_list.append(
            row_outer_border(
                row_string=line_string, outer_border=frame_border, row_divider=table_dict["row_line_divider"]
            )
        )
    for row_line_item in row_line_strings_list:
        return_string += f"{' ' * left_padding}{row_line_item}\n"
    return return_string
