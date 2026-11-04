import docx2txt

from .utils import BaseParser


class Parser(BaseParser):
    def extract(self, filename, **kwargs):
        return docx2txt.process(filename)
