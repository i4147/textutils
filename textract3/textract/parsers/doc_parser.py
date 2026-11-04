from .utils import ShellParser


class Parser(ShellParser):
    def extract(self, filename, **kwargs):
        stdout, stderr = self.run(["antiword", filename])
        return stdout
