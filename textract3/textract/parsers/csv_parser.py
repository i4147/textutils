import csv

from .utils import BaseParser


class Parser(BaseParser):
    delimiter = ","

    def extract(self, filename, **kwargs):

        with open(filename) as stream:
            reader = csv.reader(stream, delimiter=self.delimiter)
            return "\n".join(["\t".join(row) for row in reader])
