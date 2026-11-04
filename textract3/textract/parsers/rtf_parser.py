import six

from .utils import ShellParser


class Parser(ShellParser):
    def extract(self, filename, **kwargs):
        stdout, stderr = self.run(["unrtf", "--text", filename])
        splitter = six.b("-") * 17 + six.b("\n")
        text_conversion = stdout.split(splitter, 1)[-1]
        return text_conversion
