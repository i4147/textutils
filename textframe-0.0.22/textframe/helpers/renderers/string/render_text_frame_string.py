from typing import TYPE_CHECKING
from textframe.helpers.formatters.string.cell_string import cell_string_multi_line, cell_string_single_line
from textframe.helpers.formatters.string.row_outer_border import row_outer_border

if TYPE_CHECKING:
    from textframe.typing import BaseBorder, TextFrameDict


def render_text_frame_string(text_frame_dict: TextFrameDict, frame_border: BaseBorder, left_padding: int) -> str:
    line_strings_array = []
    if not text_frame_dict["max_lines"] or text_frame_dict["max_lines"] > 1:
        multiline_array = cell_string_multi_line(
            string=text_frame_dict["string"],
            width=text_frame_dict["column_list"][0]["width"],
            padding=text_frame_dict["padding"],
            align=text_frame_dict["align"],
            max_lines=text_frame_dict["max_lines"],
        )
        for multiline_item in multiline_array:
            line_strings_array.append(row_outer_border(row_string=multiline_item, outer_border=frame_border))
    else:
        row_string_inner = cell_string_single_line(
            string=text_frame_dict["string"],
            width=text_frame_dict["column_list"][0]["width"],
            padding=text_frame_dict["padding"],
            align=text_frame_dict["align"],
            trunc_value=text_frame_dict["trunc_value"],
        )
        line_strings_array.append(row_outer_border(row_string=row_string_inner, outer_border=frame_border))
    return_string = ""
    for line_string in line_strings_array:
        return_string += f"{' ' * left_padding}{line_string}\n"
    return return_string
