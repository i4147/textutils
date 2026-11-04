from .csv_parser import Parser as BaseParser


class Parser(BaseParser):
    delimiter = "|"
