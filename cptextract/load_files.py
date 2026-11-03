import pathlib
from cptextract.extract.agsfunctions import *
from cptextract.extract.csvfunctions import *
from cptextract.extract.excelfunctions import *


class CPT_import:
    version = 0.1
    depth_header = [
        "Test length[1]",
        "Test Length (m)",
        "Penetration Depth (m)",
        "H [m]",
        "Depth (m)",
        "Depth [m]",
        "Depth",
    ]
    qc_header = ["qc", "cone resistance"]
    fs_header = ["fs", "local friction", "friction resistance"]
    u2_header = ["u2", "pore pressure", "u (kPa)", "u (mpa)"]
    all = []
    CPT_IDs = []

    def __init__(self, filepath):
        self.filepath = filepath
        self.file_extension = get_file_extension(self.filepath)
        self.filename = pathlib.Path(self.filepath).stem
        self.CPT_ID = get_cptname(self.filename)
        self.engine = "None"
        self.log_msg = ""
        self.error_msg = ""
        self.warning_msg = ""
        self.CPT_IDs.append(self.CPT_ID)
        CPT_import.all.append(self)

    def add_msg(self, msg, msg_type):
        if msg_type == "e":
            self.error_msg = self.error_msg + msg
        elif msg_type == "w":
            self.warning_msg = self.warning_msg + msg
        else:
            self.log_msg = self.log_msg + msg

    def test_open(self):
        error_text = f"{self.filename}{self.file_extension} file can't be open"
        if self.file_extension == ".ags":
            from python_ags4 import AGS4

            try:
                AGS4.AGS4_to_dataframe(self.filepath)
                self.engine = "AGS4"
            except:
                print(error_text)
                self.add_msg(error_text, "e")
        elif self.file_extension == ".csv":
            import pandas as pd

            try:
                pd.read_csv(self.filepath, encoding="unicode_escape")
                self.engine = "pandas"
            except UnicodeDecodeError:
                pd.read_csv(self.filepath, encoding_errors="ignore")
                self.engine = "pandas"
            except:
                try:
                    import pyexcel as pye

                    pye.get_sheet(self.filepath)
                    self.engine = "pyexcel"
                except:
                    print(error_text)
                    self.add_msg(error_text, "e")
        elif self.file_extension == ".xls":
            from xlrd import open_workbook, XLRDError

            try:
                open_workbook(self.filepath)
                self.engine = "xlrd"
            except XLRDError:
                try:
                    import pyexcel as pye

                    pye.get_sheet(self.filepath)
                    self.engine = "pyexcel"
                except:
                    print(error_text)
                    self.add_msg(error_text, "e")
        elif self.file_extension == ".xlsx":
            import openpyxl

            try:
                openpyxl.load_workbook(self.filepath)
                self.engine = "openpyxl"
            except:
                try:
                    import pyexcel as pye

                    pye.get_sheet(self.filepath)
                    self.engine = "pyexcel"
                except:
                    print(error_text)
                    self.add_msg(error_text, "e")
        else:
            text = f"{self.filename}{self.file_extension} File Type not support!; "
            print(text)
            self.add_msg(text, "e")

    def extractcptdata(self, depth_guessword):
        if isinstance(depth_guessword, str):
            depth_guessword = [depth_guessword]
        if self.file_extension == ".ags":
            self.CPT_Data = extract_ags_cpt_data(self.filepath)
            self.data_found = True
        elif self.file_extension == ".csv" and self.engine == "pandas":
            for i in range(len(depth_guessword)):
                try:
                    self.CPT_Data = extract_csv_cpt_data(self.filepath, depth_guessword[i])
                except StopIteration:
                    self.data_found = False
                else:
                    self.data_found = True
                    self.index_location = 0
                    break
        elif self.file_extension == ".xls" and self.engine == "xlrd":
            result = ["empty"]
            for i in range(len(depth_guessword)):
                try:
                    result = extract_xls_cpt_data(self.filepath, depth_guessword[i])
                    self.CPT_Data = result[0]
                except UnboundLocalError:
                    self.data_found = False
                else:
                    self.data_found = True
                    self.index_location = result[2]
                    break
        elif self.file_extension == ".xlsx" and self.engine == "openpyxl":
            result = ["empty"]
            for i in range(len(depth_guessword)):
                try:
                    result = extract_xlsx_cpt_data(self.filepath, depth_guessword[i])
                    self.CPT_Data = result[0]
                except UnboundLocalError:
                    self.data_found = False
                else:
                    self.data_found = True
                    self.index_location = result[2]
                    break
        else:
            self.data_found = False
            print(f"No interpreter found for {self.CPT_ID}{self.file_extension}")
            pass
        if self.data_found:
            self.add_msg(f"{self.CPT_ID}{self.file_extension} successfully imported.; ", "l")
        else:
            print(f"{self.CPT_ID}{self.file_extension} data not found")

    def findcptdata(self, qc_guessword, fs_guessword, u2_guessword):
        dict1 = {}
        if self.file_extension != ".ags" and self.data_found:
            dict1["depth_index"] = self.index_location
            dict1["qc_index"] = find_header_dataframe(self.CPT_Data, qc_guessword)
            dict1["fs_index"] = find_header_dataframe(self.CPT_Data, fs_guessword)
            dict1["u2_index"] = find_header_dataframe(self.CPT_Data, u2_guessword)
            print(self.CPT_ID)
            print(dict1.values())
            self.index_location = dict1

    def compilecptdata(self):
        self.depth_series = []
        self.qc_series = []
        self.fs_series = []
        self.u2_series = []
        self.okay_calc = False
        if self.file_extension != ".ags" and self.data_found:
            if 99 in list(self.index_location.values()):
                self.add_msg(f"{self.CPT_ID}{self.file_extension} could not detect column headers!; ", "e")
                pass
            else:
                self.qc_units = identify_units(self.CPT_Data.iloc[:, self.index_location["qc_index"]])
                self.fs_units = identify_units(self.CPT_Data.iloc[:, self.index_location["fs_index"]])
                self.u2_units = identify_units(self.CPT_Data.iloc[:, self.index_location["u2_index"]])
                self.depth_series = self.CPT_Data.iloc[:, self.index_location["depth_index"]]
                self.qc_series = self.CPT_Data.iloc[:, self.index_location["qc_index"]]
                self.fs_series = self.CPT_Data.iloc[:, self.index_location["fs_index"]]
                self.u2_series = self.CPT_Data.iloc[:, self.index_location["u2_index"]]
                starting_index = find_first_num_row(self.qc_series)
                try:
                    self.CPT_dataframe = self.CPT_Data.iloc[starting_index:, list(self.index_location.values())].astype(
                        "float"
                    )
                except ValueError:
                    error_text = f"{self.CPT_ID}{self.file_extension} non-numeric data present!; "
                    print(error_text)
                    self.add_msg(error_text, "e")
                    self.add_msg(f"{self.CPT_ID}{self.file_extension} not extracted!; ", "l")
                else:
                    self.depth_series = self.CPT_Data.iloc[starting_index:, self.index_location["depth_index"]]
                    qc_result = auto_convert(
                        self.CPT_Data.iloc[starting_index:, self.index_location["qc_index"]], self.qc_units, 150
                    )
                    self.qc_series = qc_result[0]
                    self.add_msg(qc_result[1], "w")
                    self.CPT_dataframe.iloc[:, 1] = self.qc_series
                    fs_result = auto_convert(
                        self.CPT_Data.iloc[starting_index:, self.index_location["fs_index"]], self.fs_units, 15
                    )
                    self.fs_series = fs_result[0]
                    self.add_msg(fs_result[1], "w")
                    self.CPT_dataframe.iloc[:, 2] = self.fs_series
                    u2_result = auto_convert(
                        self.CPT_Data.iloc[starting_index:, self.index_location["u2_index"]], self.u2_units, 15
                    )
                    self.u2_series = u2_result[0]
                    self.add_msg(u2_result[1], "w")
                    self.CPT_dataframe.iloc[:, 3] = self.u2_series
                    self.okay_calc = True
                    self.add_msg(f"{self.CPT_ID}{self.file_extension} successfully extracted.; ", "l")
        elif self.file_extension == ".ags" and self.data_found:
            self.depth_series = self.CPT_Data["SCPT_DPTH"]
            self.qc_series = self.CPT_Data["SCPT_RES"]
            self.fs_series = self.CPT_Data["SCPT_FRES"]
            self.u2_series = self.CPT_Data["SCPT_PWP2"]
            self.CPT_dataframe = self.CPT_Data.loc[:, ["SCPT_DPTH", "SCPT_RES", "SCPT_FRES", "SCPT_FRES"]]
            self.add_msg(f"{self.CPT_ID}{self.file_extension} successfully extracted.; ", "l")
            self.okay_calc = True

    def auto_extract(self):
        self.test_open()
        self.extractcptdata(CPT_import.depth_header)
        self.findcptdata(
            qc_guessword=CPT_import.qc_header, fs_guessword=CPT_import.fs_header, u2_guessword=CPT_import.u2_header
        )
        self.compilecptdata()

    @classmethod
    def all_from_folder(cls, folderpath, accepted_extensions):
        all_paths = get_filepaths(folderpath)
        for filepaths in all_paths:
            if get_file_extension(filepaths) in accepted_extensions:
                CPT_import(filepaths)
            else:
                pass

    def __repr__(self):
        return f"CPT_import('{self.CPT_ID}', '{self.file_extension}')"


def get_cptname(filename):
    import os

    try:
        temp2 = filename.split("_")
        cptname = temp2[0] + "_" + temp2[1]
    except IndexError:
        temp2 = filename
        cptname = os.path.splitext(temp2)[0]
    return cptname


def get_file_extension(filepath):
    import pathlib

    file_extension = pathlib.Path(filepath).suffix
    return file_extension.lower()


def get_filepaths(directory):
    import os

    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths


def find_header_dataframe(df, headers):
    if isinstance(headers, str):
        headers = [headers]
    df_headers = list(df.columns)
    header_index = 99
    for x in range(len(df_headers)):
        header_text = df_headers[x].lower()
        if bool([ele for ele in headers if (ele.lower() in header_text)]):
            header_index = x
            break
    return header_index


def find_first_num_row(input_list, limit=10):
    startrow = 0
    i = 0
    while i < limit:
        checkstartrow = input_list[i]
        try:
            float(checkstartrow)
            startrow = i
            break
        except ValueError:
            i += 1
    if i > 5:
        print(str(i) + " starting row unclear! Please check")
    return startrow


def identify_units(df_series):
    series_unit = "Not Defined"
    header = df_series.name.lower()
    if "mpa" in header:
        series_unit = "mpa"
    elif "kpa" in header:
        series_unit = "kpa"
    else:
        try:
            if any(df_series.str.contains("mpa", case=False) == True):
                series_unit = "mpa"
            elif any(df_series.str.contains("kpa", case=False) == True):
                series_unit = "kpa"
            else:
                series_unit = "Not Defined"
        except AttributeError:
            series_unit = "Not Defined"
    return series_unit


def auto_convert(df, unit, limit):
    msg = ""
    header = df.name
    if unit == "kpa":
        df = df * 0.001
    if df.max() > limit and unit == "mpa":
        df = df * 0.001
        msg = f"{header} units have been mislabelled! Please check!; "
    if df.max() > limit and unit == "Not Defined":
        df = df * 0.001
        msg = f"{header} units inferred as kpa.; "
    return [df, msg]


def visualise_dict(d, lvl=0):
    for k in sorted(d):
        if lvl == 0 and k == sorted(d)[0]:
            print("{:<25} {:<15} {:<10}".format("KEY", "LEVEL", "TYPE"))
            print("-" * 79)
        indent = "  " * lvl
        t = str(type(d[k]))
        print("{:<25} {:<15} {:<10}".format(indent + str(k), lvl, t))
        if type(d[k]) == dict:
            visualise_dict(d[k], lvl + 1)
