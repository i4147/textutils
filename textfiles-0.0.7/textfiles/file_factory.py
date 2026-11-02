import json, csv
import os.path
from .csv_file import CsvFile
from .json_file import JsonFile
from .txt_file import TxtFile
from .exceptions import *


class TextFile:
    @staticmethod
    def make_file_instance(
        filetype: str, path: str, has_header: bool = True, delimiter: str = ",", max_size: int = 50
    ) -> CsvFile | TxtFile | JsonFile:
        max_size = max_size * 1000000
        size = os.path.getsize(path)
        if size > max_size:
            raise SizeError(path)
        if filetype == "csv":
            return CsvFile(path, delimiter, has_header)
        elif filetype == "txt":
            return TxtFile(path)
        elif filetype == "json":
            return JsonFile(path)
        else:
            raise InvalidTypeError(filetype)

    @staticmethod
    def make_file(filetype: str, path: str, header: list = None) -> CsvFile | TxtFile | JsonFile:
        if filetype == "csv":
            with open(path, "w", newline="") as cv:
                write = csv.DictWriter(cv, fieldnames=header)
                write.writeheader()
                return CsvFile(path)
        elif filetype == "txt":
            fh = open(path, "x")
            fh.close()
            return TxtFile(path)
        elif filetype == "json":
            with open(path, "w") as js:
                json.dump(None, js)
            return JsonFile(path)
        else:
            raise InvalidTypeError(filetype)
