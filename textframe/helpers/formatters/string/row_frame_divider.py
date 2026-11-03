import time
from typing import TYPE_CHECKING
from textframe.characters.line_h import h_line
from textframe.characters.matrix_cross import cross_matrix

if TYPE_CHECKING:
    from textframe.typing import BaseBorder


def row_frame_divider(divider: BaseBorder, column_list_top: list, column_list_bottom: list) -> str:
    return_string = ""
    cumulative_top_count = 0
    cumulative_top = []
    for v_line_index in range(len(column_list_top)):
        cumulative_top_count += column_list_top[v_line_index]["width"]
        cumulative_top.append([
            column_list_top[v_line_index]["width"],
            cumulative_top_count,
            column_list_top[v_line_index]["divider"],
        ])
    cumulative_top.reverse()
    cumulative_bottom_count = 0
    cumulative_bottom = []
    for v_line_index in range(len(column_list_bottom)):
        cumulative_bottom_count += column_list_bottom[v_line_index]["width"]
        cumulative_bottom.append([
            column_list_bottom[v_line_index]["width"],
            cumulative_bottom_count,
            column_list_bottom[v_line_index]["divider"],
        ])
    cumulative_bottom.reverse()
    current_v_line_index = len(column_list_top) + len(column_list_bottom)
    while current_v_line_index > 0:
        if len(cumulative_top) > 0 and len(cumulative_bottom) > 0:
            if cumulative_top[-1][1] > cumulative_bottom[-1][1]:
                return_string += f"{h_line[divider] * cumulative_bottom[-1][0]}{cross_matrix['blank'][divider][cumulative_bottom[-1][2]]}"
                cumulative_top[-1][0] = cumulative_top[-1][0] - cumulative_bottom[-1][0] - 1
                cumulative_bottom.pop()
            elif cumulative_top[-1][1] == cumulative_bottom[-1][1]:
                return_string += f"{h_line[divider] * cumulative_bottom[-1][0]}{cross_matrix[cumulative_top[-1][2]][divider][cumulative_bottom[-1][2]]}"
                cumulative_top.pop()
                cumulative_bottom.pop()
            elif cumulative_top[-1][1] < cumulative_bottom[-1][1]:
                return_string += (
                    f"{h_line[divider] * cumulative_top[-1][0]}{cross_matrix[cumulative_top[-1][2]][divider]['blank']}"
                )
                cumulative_bottom[-1][0] = cumulative_bottom[-1][0] - cumulative_top[-1][0] - 1
                cumulative_top.pop()
        else:
            if len(cumulative_top) > 0:
                return_string += (
                    f"{h_line[divider] * cumulative_top[-1][0]}{cross_matrix[cumulative_top[-1][2]][divider]['blank']}"
                )
                if cumulative_top[-1][0] < 0:
                    return_string = return_string[0 : cumulative_top[-1][0]]
                cumulative_top.pop()
            if len(cumulative_bottom) > 0:
                return_string += f"{h_line[divider] * cumulative_bottom[-1][0]}{cross_matrix['blank'][divider][cumulative_bottom[-1][2]]}"
                if cumulative_bottom[-1][0] < 0:
                    return_string = return_string[0 : cumulative_bottom[-1][0]]
                cumulative_bottom.pop()
        current_v_line_index -= 1
    return return_string[0:-1]
