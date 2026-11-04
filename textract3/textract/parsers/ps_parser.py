from .utils import ShellParser


class Parser(ShellParser):
    def extract(self, filename, **kwargs):
        stdout, _ = self.run(["ps2ascii", filename])
        return stdout
