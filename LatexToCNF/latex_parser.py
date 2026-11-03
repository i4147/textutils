from typing import List, Union
import pyparsing as pp

pp.ParserElement.enablePackrat()
Formula = Union[str, List[Union[str, "Formula", List["Formula"]]]]


class LatexParser:
    variables = pp.Word(pp.alphas, max=1)
    _negation = pp.Word(r"~\neg", max=0).setParseAction(lambda token: "\neg")
    _and = pp.Word(r"&\wedge").setParseAction(lambda token: "\wedge")
    _or = pp.Word(r"|\vee").setParseAction(lambda token: "\\vee")
    _implies = pp.Word(r">\rightarrow").setParseAction(lambda token: "\rightarrow")
    operators = [
        (_negation, 1, pp.opAssoc.RIGHT),
        (_and, 2, pp.opAssoc.LEFT),
        (_or, 2, pp.opAssoc.LEFT),
        (_implies, 2, pp.opAssoc.LEFT),
    ]
    parser = pp.infixNotation(variables | _negation, operators)

    def parse(self, line: str) -> Formula:
        try:
            return self.parser.parseString(line).asList()
        except pp.ParseException:
            return None

    def parse_file(self, file_path: str) -> list[Formula]:
        try:
            with open(file=file_path, mode="r") as file:
                lines = file.readlines()
                parses = [self.parse(line) for line in lines]
            return parses
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
