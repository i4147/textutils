from latextomd import config
from TexSoup import TexSoup


class Latex(object):
    def __init__(self, latex_string):
        self.soup = TexSoup(latex_string)

    def _delete_commands(self):
        for command in config.del_commands:
            try:
                for include in self.soup.find_all(command):
                    include.delete()
            except ValueError:
                pass

    def _replace_commands(self):
        for command in config.replace_commands:
            print(command[0])
            liste_commands = self.soup.find_all(command[0])
            self.content = str(self.soup)
            for match in liste_commands:
                self.content = self.content.replace(str(match), command[1].replace("S_T_R", match.string))
            self.soup = TexSoup(self.content)

    def process(self):
        self._delete_commands()
        self._replace_commands()
        self.content = str(self.soup)
        math_inline = self.soup.find_all("$")
        for match in math_inline:
            string = str(list(match.descendants)[0])
            self.content = self.content.replace(string, string.strip())

        return self.content
