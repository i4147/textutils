from . import latex_parser as lp
import re


def iscommand(string: str) -> bool:
    return re.match(pattern=r"^\\", string=string)


def well_formed_formula(parse: lp.Formula) -> bool:
    if parse is None:
        return False
    if isinstance(parse, list):
        match len(parse):
            case 1:
                return well_formed_formula(parse=parse[0])
            case 2:
                if form(parse) != "NEGATION":
                    return False
                return well_formed_formula(parse=parse[1])
            case 3:
                if form(parse) not in ["CONJUNCTION", "DISJUNCTION", "IMPLIES"]:
                    return False
                return well_formed_formula(parse=parse[0]) and well_formed_formula(parse=parse[2])
            case _:
                return False
    elif isinstance(parse, str):
        return not iscommand(parse)
    else:
        return False


def negation(phi: lp.Formula):
    return ["\\neg", phi]


def conjunction(phi: lp.Formula, psi: lp.Formula):
    return [phi, "\\wedge", psi]


def disjunction(phi: lp.Formula, psi: lp.Formula):
    return [phi, "\\vee", psi]


def implies(phi: lp.Formula, psi: lp.Formula):
    return [phi, "\\rightarrow", psi]


def form(formula: lp.Formula) -> str:
    if isinstance(formula, list):
        if formula[0] == lp.LatexParser._negation:
            return "NEGATION"
        if formula[1] == lp.LatexParser._and:
            return "CONJUNCTION"
        if formula[1] == lp.LatexParser._or:
            return "DISJUNCTION"
        if formula[1] == lp.LatexParser._implies:
            return "IMPLIES"
    if isinstance(formula, str) and not iscommand(formula):
        return "ATOM"
    return None
