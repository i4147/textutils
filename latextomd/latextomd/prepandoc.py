import codecs
import os
import re


class Prepandoc(object):
    def __init__(self, latex_string="", export_file=""):
        self.content = latex_string
        self.export_file = export_file

    def process(self):
        if "\\begin{document}" in self.content:
            self.preamble, self.content = self.content.split("\\begin{document}")
        else:
            self.preamble = "\\documentclass{article}"
            self.content = self.content + "\n\\end{document}"
