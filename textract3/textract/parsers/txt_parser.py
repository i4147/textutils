from .utils import BaseParser


class Parser(BaseParser):
    def extract(self, filename, **kwargs):
        with open(filename) as stream:
            return stream.read()
