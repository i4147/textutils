import codecs
import os
import re
import subprocess

from latextomd import config
from latextomd.latexblocks import LatexBlocks


class LatexString(object):
    def __init__(self, latex_string, preamble, export_file_name):
        self.content = latex_string
        self.preamble = preamble
        self.nbfigure = 0
        self.export_file_name = export_file_name
        self.figure = []

    def process(self):
        self._remove_comments()
        self._replace_simple()
        self._math_replace()
        self._convertList()
        # self._convertItemize()
        self._convertEnumerate()
        self.content = LatexBlocks(self.content).process()
        self._findTikz()
        self.findPstricks()
        self.replaceFigure()
        return self.content

    def _remove_comments(self):
        self.content = re.sub("(?<!\\\\)%.*$", "", self.content, flags=re.M)

    def _replace_simple(self):
        for replace_simple in config.replace_simple:
            self.content = self.content.replace(replace_simple[0], replace_simple[1])

    def _math_replace(self):
        for item in config.math_sub:
            p = re.compile(item[0])
            self.content = p.sub(item[1], self.content)

    def _convertItemize(self):
        new_lines = []
        self.lines = self.content.splitlines()

        for line in self.lines:
            if r"\begin{itemize}" in line:
                line = "\n\n"
            elif r"\end{itemize}" in line:
                line = "\n\n"
            elif r"\item" in line:
                line = line.replace(r"\item", "\n\n$\\bullet$ ")
            new_lines.append(line)
        self.lines = new_lines
        self.content = "\n".join(self.lines)

    def _convertList(self):
        new_lines = []
        in_list = False
        self.lines = self.content.splitlines()

        for line in self.lines:
            if r"\begin{list}" in line:
                line = "\n\n"
                in_list = True
            elif r"\end{list}" in line:
                line = "\n\n"
                in_list = False
            elif r"\item" in line and in_list:
                line = line.replace(r"\item", "\n\n$\\bullet$ ")
            new_lines.append(line)
        self.lines = new_lines
        self.content = "\n".join(self.lines)

    def _convertEnumerate(self):
        level_enumerate = 0
        enumi = 0
        enumii = 0
        new_lines = []
        in_itemize = False
        arabic = "abcdefghijklmnopqrstuvwxz"
        self.lines = self.content.splitlines()

        for line in self.lines:
            if r"\begin{enumerate}" in line or r"\begin{colenumerate}" in line:
                level_enumerate = level_enumerate + 1
                if "start" in line:
                    print(level_enumerate)
                    if level_enumerate == 1:
                        enumi = int(line.split("=")[1].split("]")[0]) - 1
                    else:
                        enumii = int(line.split("=")[1].split("]")[0]) - 1

                line = ""

            elif r"\end{enumerate}" in line or r"\end{colenumerate}" in line:
                if level_enumerate == 2:
                    enumii = 0
                else:
                    enumi = 0
                level_enumerate = level_enumerate - 1
                line = ""
            elif r"\begin{itemize" in line:
                in_itemize = True
            elif r"\end{itemize" in line:
                in_itemize = False
            elif r"\item" in line and level_enumerate != 0 and not in_itemize:
                if level_enumerate == 1:
                    enumi = enumi + 1
                    line = line.replace(r"\item", r"\textbf{" + f"{enumi}. " + "}")
                    line = "\n\n" + line
                else:
                    line = line.replace(r"\item", r"\textbf{" + f"{enumi}.{arabic[enumii]}) " + "}")
                    enumii = enumii + 1
                    line = "\n\n" + line
            new_lines.append(line)
        self.lines = new_lines
        self.content = "\n".join(self.lines)

    def findPstricks(self):
        in_pstricks = False
        lignes_pstricks = []
        pstricks = []
        for line in self.lines:
            if in_pstricks:
                lignes_pstricks.append(line)
                if r"\end{pspicture" in line:
                    in_pstricks = False
                    pstricks.append("\n".join(lignes_pstricks))
                    lignes_pstricks = []
            else:
                if r"\psset" in line or r"\begin{pspicture" in line:
                    in_pstricks = True
                    lignes_pstricks.append(line)
        self.figure = self.figure + pstricks

    def _findTikz(self):
        self.lines = self.content.splitlines()
        in_tikz = False
        lignes_tikz = []
        tikz = []
        for line in self.lines:
            if in_tikz:
                lignes_tikz.append(line)
                if r"\end{tikz" in line:
                    in_tikz = False
                    tikz.append("\n".join(lignes_tikz))
                    lignes_tikz = []
            else:
                if r"\begin{tikz" in line:
                    in_tikz = True
                    lignes_tikz.append(line)
        self.tikz = tikz
        self.figure = self.figure + self.tikz

    def replaceFigure(self):
        if len(self.figure) == 0:
            return
        total = (
            self.preamble.replace("[dvips]", "")
            + "\n\\begin{document}\n\\thispagestyle{empty}\n"
            + "\n\\newpage\\thispagestyle{empty}\n".join(self.figure)
            + "\n\\newpage\\thispagestyle{empty}\nEMPTY\n\\end{document}"
        )
        if not os.path.exists("temp"):
            os.mkdir("temp")

        f = codecs.open("prepandoc.tex", "w", "utf-8")
        f.write(total)
        f.close()
        os.system("lualatex prepandoc.tex")
        os.system("pdfcrop prepandoc.pdf")
        print(self.export_file_name)
        command = "magick convert -density 600 prepandoc-crop.pdf " + self.export_file_name.replace(".md", "") + ".jpg"
        os.system(command)
        # os.system("magick convert -density 600 prepandoc-crop.pdf truc-%p.jpg")
        for figure in self.figure:
            self.content = self.content.replace(
                figure,
                "\\includegraphics{./" + self.export_file_name.replace(".md", "") + "-" + str(self.nbfigure) + "}\n",
            )
            self.nbfigure = self.nbfigure + 1

        """ os.system("dvisvgm temp")
            try:
                os.rename("temp.svg", "figure"+str(self.nbfigure)+".svg")
            except:
                print("Le fichier figure"+str(self.nbfigure)+".svg existe déjà")
            self.content = self.content.replace(
                figure,
                '![Image](./figure'+str(self.nbfigure)+".svg)") """
