import copy
import math
from typing import List, TypeVar

T = TypeVar("T")


def calc_column_width_error():
    msg = f"Error computing width values. Please input check widths."
    raise Exception(msg)


def calc_column_widths(columns: list[T], frame_width: int, column_padding: int) -> list[T]:
    columns = copy.deepcopy(columns)
    min_column_width = (column_padding * 2) + 1
    total_defined_column_width = 0
    undefined_width_columns = []
    error = False
    for column_index, column_item in enumerate(columns):
        if "width" in column_item:
            validated_value = False
            if type(column_item["width"]) == str and column_item["width"][-1] == "%":
                try:
                    width_percentage = math.floor(frame_width / (100 / int(column_item["width"][0:-1]))) - 2
                    column_item["width"] = width_percentage
                    validated_value = True
                except:
                    error = True
            if type(column_item["width"]) == int:
                if column_item["width"] < min_column_width:
                    error = True
                total_defined_column_width += column_item["width"]
                validated_value = True
            if not validated_value:
                error = True
        else:
            undefined_width_columns.append(column_index)
    if error:
        calc_column_width_error()
    total_column_width = 0
    if undefined_width_columns:
        calculated_width_total = frame_width - (total_defined_column_width + len(columns) + 1)
        calculated_column_width = math.floor((calculated_width_total / len(undefined_width_columns)))
        if calculated_column_width < min_column_width:
            error = True
        for column_index, column_item in enumerate(columns):
            if column_index in undefined_width_columns:
                column_item["width"] = calculated_column_width
            total_column_width += column_item["width"]
    else:
        total_column_width = total_defined_column_width
    if error:
        calc_column_width_error()
    if total_column_width + len(columns) + 1 > frame_width:
        calc_column_width_error()
    if total_column_width + len(columns) + 1 < frame_width:
        if len(undefined_width_columns) > 0:
            columns[undefined_width_columns[0]]["width"] += (frame_width - total_column_width) - (len(columns) + 1)
        else:
            calc_column_width_error()
    return columns
