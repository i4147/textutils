from radtext.models.neg.ngrex.pattern import NgrexPattern, NgrexMatch
from . import parser
from . import pattern


def compile(ngrex: str) -> NgrexPattern:
    """
    Compiles the given expression into a pattern
    """
    p = parser.yacc.parse(ngrex)
    pattern.validate_names(p)
    return p
