import os

from .utils import ShellParser


class Parser(ShellParser):
    def extract(self, filename, **kwargs):

        if "language" in kwargs:
            args = ["tesseract", filename, "stdout", "-l", kwargs["language"]]
        else:
            args = ["tesseract", filename, "stdout"]

        stdout, _ = self.run(args)
        return stdout
