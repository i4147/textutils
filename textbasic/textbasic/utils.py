import time
import csv
import pandas as pd


__all__ = ["read_df"]


def read_df(path):
    extention = path.split(".")[-1]
    if extention in ["csv", "CSV"]:
        switch = "csv"
    elif extention in ["xlsx", "xls"]:
        switch = "excel"
    else:
        raise ValueError(f"{extention}은(는) 잘못되거나 지정되지 않은 확장자입니다.")

    if switch == "csv":
        encoding = "utf-8-sig"
        while True:
            try:
                data_df = pd.read_csv(path, encoding=encoding)
                break
            except UnicodeDecodeError:
                encoding = "cp949"
            except pd.errors.ParserError:
                f = open(path, encoding=encoding)
                reader = csv.reader(f)
                csv_list = []
                for line in reader:
                    if len(line) != 38:
                        pass
                    csv_list.append(line)
                f.close()
                data_df = pd.DataFrame(csv_list)
                data_df.columns = data_df.iloc[0].to_list()
                data_df = data_df.drop(index=data_df.index[0])
                break
    if switch == "excel":
        data_df = pd.read_excel(path)

    return data_df
