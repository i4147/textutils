import codecs
import os
import re

from latextomd import config

from latextomd.postpandoc import Postpandoc
from latextomd.soup import Latex
from latextomd.text_manipulation import LatexString


def _process_preamble(latex_string):
    if r"\begin{document}" in latex_string:
        preamble, content = latex_string.split(r"\begin{document}")
        if r"\end{document}" in content:
            content = content.split(r"\end{document}")[0]
    else:
        preamble = "\\documentclass{article}\n"
        content = latex_string
    return preamble, content


def _strip_lines(latex_string):
    lines = latex_string.splitlines()
    result = []
    for line in lines:
        result.append(line.strip())
    return "\n".join(result)


def _clean_lines(latex_string):
    lines = latex_string.splitlines()
    while lines[0] == "":
        lines = lines[1:]
    while lines[-1] == "":
        lines = lines[:-1]
    content = "\n".join(lines)
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")
    return content


def _delete_blocks(latex_string):
    content = latex_string
    for env in config.del_environnements:
        content = content.replace(env, "")
    return content


def _pandoc(preamble, content):
    total = "\n\\begin{document}\n".join([preamble, content]) + "\n\\end{document}"
    f = codecs.open("temp.tex", "w", "utf-8")
    f.write(total)
    f.close()
    # os.system("pandoc temp.tex -o temp.md --katex --from latex --to gfm")
    os.system("pandoc temp.tex -o temp.md")
    with codecs.open("temp.md", "r", "utf-8") as f:
        content = f.read()
    return content
    # os.system(f"dvisvgm temp.dvi")


def to_markdown(latex_string, export_file_name=""):
    content = latex_string
    content = _strip_lines(content)

    preamble, content = _process_preamble(content)
    content = LatexString(content, preamble, export_file_name).process()
    content = _pandoc(preamble, content)
    # content = Latex(content).process()
    content = Postpandoc(content).process()
    content = _delete_blocks(content)
    # content = _strip_lines(content)

    content = _clean_lines(content)
    return content


class LatexToMd(object):
    def __init__(self, latex_string, export_file_name="", options={}):
        self.content = latex_string
        self.options = options
        self._process_options()

    def _process_options(self):
        try:
            self.pandoc_enumerate = self.options["pandoc_enumerate"]
        except:
            self.pandoc_enumerate = False

    def process(self):
        self.prepandoc()
        return self.content

    def prepandoc(self):
        self._remove_comments()
        self._replace_simple()
        self._strip_lines()
        self.preamble, self.content = _process_preamble(self.content)
        self.content = _clean_lines(self.content)

    def _remove_comments(self):
        self.content = re.sub("(?<!\\\\)%.*$", "", self.content, flags=re.M)

    def _replace_simple(self):
        for replace_simple in config.replace_simple:
            self.content = self.content.replace(replace_simple[0], replace_simple[1])

    def _strip_lines(self):
        lines = self.content.splitlines()
        result = []
        for line in lines:
            result.append(line.strip())
        self.content = "\n".join(result)
