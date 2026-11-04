import re


# from latextomd import config


class LatexBlocks(object):
    def __init__(self, latex_string):
        self.content = latex_string
        self.exercice = 0

    def process(self):
        if "\\begin{exercice}" in self.content:
            self.process_exercice()
        return self.content

    def process_exercice(self):
        regex_exercice = r"\\begin{exercice}(\[(?P<block_title>.*?)\])?(\[(?P<block_bareme>.*?)\])?"
        self.content = self.content.replace("\\end{exercice}", "\n\n:::\n\n")
        self.lines = self.content.split("\n")
        newlines = []
        for line in self.lines:
            if "\\begin{exercice}" in line:
                matches = re.finditer(regex_exercice, line, re.MULTILINE)
                self.exercice = self.exercice + 1
                for matchNum, match in enumerate(matches, start=1):
                    if match.group(2) and match.group(4):
                        line = f":::exercice Exercice {self.exercice}: {match.group(2)} /{match.group(4)} points\n\n"

                    elif match.group(2) and not match.group(4):
                        line = f":::exercice Exercice {self.exercice}: {match.group(2)}\n\n"
                    elif not match.group(2) and match.group(4):
                        line = f":::exercice Exercice {self.exercice}: /{match.group(4)} points\n\n"
                    else:
                        line = f":::exercice Exercice {self.exercice}:\n\n"

            newlines.append(line)
        self.lines = newlines
        self.content = "\n".join(self.lines)
