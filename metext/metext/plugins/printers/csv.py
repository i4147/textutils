import sys
from csv import QUOTE_MINIMAL, DictWriter
from csv import writer as csvwriter
from typing import List, Union

from metext.plugin_base import BasePrinter


class CsvPrinter(BasePrinter):
    PLUGIN_NAME = "csv"

    @classmethod
    def run(cls, _input: Union[List[list], List[dict]], **kwargs):
        out_file = kwargs.get("filename", "-")
        if not _input:
            return
        with sys.stdout if out_file == "-" else open(out_file, "w", encoding="utf8", newline="") as f:
            if isinstance(_input[0], dict):
                fieldnames = list(_input[0].keys())
                writer = DictWriter(f, fieldnames=fieldnames, quoting=QUOTE_MINIMAL, lineterminator="\n")
                writer.writeheader()
            else:
                writer = csvwriter(f, quoting=QUOTE_MINIMAL, lineterminator="\n")
            writer.writerows(_input)
