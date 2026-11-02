import pandas as pd
from settings.settings import list_drop, path_read
from utils import Utils
from .step import Step


class Process_(Step, Utils):
    def process(self, data, inputs, utils):
        file_name = inputs["file_name"]
        data, _data_row = self.read_data(file_name)
        data = self.drop_data(data)
        return data

    def read_data(self, file_name):
        try:
            data = pd.read_csv(f"{path_read}{file_name}", encoding="utf-8", engine="python")
        except:
            data = pd.read_excel(f"{path_read}{file_name}")
        return data, len(data.columns)

    def drop_data(self, data):
        for i in list_drop:
            try:
                data = data.drop(i, axis=1)
            except:
                print(f"Dropped_Error: No {i}")
        print(f"process_CF:【columns_dropped:】\n {data.columns}")
        try:
            data = data[(data["幅寬"] != "針內57/全幅59不預留")]
            data = data.replace("58/59", "58.5")
            data = data.replace("全幅", "")
            data = data.replace("不預留", "")
            data = data.replace("全幅56不預留", "56")
            data = data.replace("全幅63.5", "63.5")
            data = data.replace("全幅63", "63")
            data["幅寬"] = data["幅寬"].astype(float)
        except:
            print("astype_Error: 幅寬 Cannot astype(int)")
        try:
            data["顏色"] = data["F_COLOR_CHI"]
            data = data.drop("F_COLOR_CHI", axis=1)
        except:
            print("process_CF: Error: col_name no 顏色")
        data = super().colcul_kcal(data)
        return data
