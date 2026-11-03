import glob
import os
from pipeline.pipeline import Pipeline
from pipeline.steps.filter_ import Filter_
from pipeline.steps.group import Group
from pipeline.steps.preflight import Preflight
from pipeline.steps.process import Process_
from pipeline.steps.transform import Transform_
from settings.settings import path_read
from utils import Utils


def main():
    steps = [Preflight(), Process_(), Filter_(), Transform_(), Group()]
    inputs = {"file_name": file_name, "data_save_name": data_save_name}
    utils = Utils(inputs)
    p = Pipeline(steps)
    data = p.run(inputs, utils)
    return data


if __name__ == "__main__":
    os.chdir(path_read)
    file = glob.glob("*screened*")
    excel_type = ".xlsx"
    company = "CF"
    process_ = "(filted)"
    for file_name in file:
        data_save_name = file_name[:4] + file_name[13:19] + file_name[21:23]
        data_save_name = f"{company}{process_}{data_save_name}{excel_type}"
        data = main()
        print(f"\n{'-' * 5} Finish Textile Process {'-' * 5}")
