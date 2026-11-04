# -*- coding: utf-8 -*-

from doctext.utils import run_checked
from termcolor import cprint


class Capabilities:
    def __init__(self, openai: bool = False):

        self._c = {}
        self._c["openai"] = openai
        self.initialize()

    def check_capability(self, capability: str, args: list) -> bool:
        self._c[capability] = False
        try:
            run_checked(args)
            self._c[capability] = True
        except:
            cprint(f"Commandline tool '{args[0]}' not found. Some things might break.", "red")
            pass
        return self._c[capability]

    def initialize(self):
        self.check_capability("ffmpeg", ["ffmpeg", "-version"])
        self.check_capability("convert", ["convert", "-version"])
        self.check_capability("pdftotext", ["pdftotext", "-v"])
        self.check_capability("heif_convert", ["heif-convert", "-v"])
        self.check_capability("dcraw", ["dcraw"])
