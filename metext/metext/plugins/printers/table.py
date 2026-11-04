import sys
from typing import List

from tabulate import tabulate

from metext.plugin_base import BasePrinter


class TextTablePrinter(BasePrinter):
    PLUGIN_NAME = "text"

    @classmethod
    def run(cls, _input: List[list], **kwargs):
        out_file = kwargs.get("filename", "-")
        tablefmt = kwargs.get("tablefmt", "grid")
        has_header = kwargs.get("has_header", True)
        if not _input:
            return

        with sys.stdout if out_file == "-" else open(out_file, "w", encoding="utf8") as f:
            if has_header:
                f.write(tabulate(_input[1:], headers=_input[0], tablefmt=tablefmt))
            else:
                f.write(tabulate(_input, tablefmt=tablefmt))
