import pandas as pd
from settings.settings import list_rpm, list_temp, path_log, set_rules
from .step import Step


class Filter_(Step):
    def process(self, data, inputs, utils):
        data = data.dropna()
        data = data.reset_index(drop=True)
        for set_rule in range(len(set_rules["col"])):
            data = self.filter_base(
                data,
                utils,
                data.index.size,
                set_rules["col"][set_rule],
                set_rules["max"][set_rule],
                set_rules["min"][set_rule],
            )
        return data

    def filter_base(self, data, utils, data_row, col_name, up_limit, low_limit):
        try:
            data = data[(data[col_name] < up_limit) & (data[col_name] > low_limit)]
            data = data.reset_index(drop=True).round(1)
            utils.check_list(data, col_name, data_row)
        except KeyError as err:
            print("filter_CF: Exception:", err)
        return data
