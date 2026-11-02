from . import latex_parser as lp
from .formula_validetor import *


def IMPL_FREE(formula: lp.Formula) -> lp.Formula:
    FORM = form(formula)
    match FORM:
        case "NEGATION":
            return negation(IMPL_FREE(formula[1]))
        case "CONJUNCTION":
            return conjunction(IMPL_FREE(formula[0]), IMPL_FREE(formula[2]))
        case "DISJUNCTION":
            return disjunction(IMPL_FREE(formula[0]), IMPL_FREE(formula[2]))
        case "IMPLIES":
            return disjunction(negation(IMPL_FREE(formula[0])), IMPL_FREE(formula[2]))
        case "ATOM":
            return formula
        case _:
            return None


def NNF(formula: lp.Formula) -> lp.Formula:
    FORM = form(formula)
    match FORM:
        case "NEGATION":
            sub_formula = formula[1]
            sub_form = form(sub_formula)
            match sub_form:
                case "NEGATION":
                    return NNF(sub_formula[1])
                case "CONJUNCTION":
                    return disjunction(NNF(negation(sub_formula[0])), NNF(negation(sub_formula[2])))
                case "DISJUNCTION":
                    return conjunction(NNF(negation(sub_formula[0])), NNF(negation(sub_formula[2])))
                case "ATOM":
                    return negation(sub_formula)
        case "CONJUNCTION":
            return conjunction(NNF(formula[0]), NNF(formula[2]))
        case "DISJUNCTION":
            return disjunction(NNF(formula[0]), NNF(formula[2]))
        case "ATOM":
            return formula
        case _:
            return None


def DISTR(eta_1: lp.Formula, eta_2: lp.Formula) -> lp.Formula:
    if form(eta_1) == "CONJUNCTION":
        return conjunction(DISTR(eta_1[0], eta_2), DISTR(eta_1[2], eta_2))
    if form(eta_2) == "CONJUNCTION":
        return conjunction(DISTR(eta_1, eta_2[0]), DISTR(eta_1, eta_2[2]))
    return disjunction(eta_1, eta_2)


def CNF(formula: lp.Formula) -> lp.Formula:
    FORM = form(formula)
    match FORM:
        case "CONJUNCTION":
            return conjunction(CNF(formula[0]), CNF(formula[2]))
        case "DISJUNCTION":
            return DISTR(CNF(formula[0]), CNF(formula[2]))
        case "NEGATION":
            return formula
        case "ATOM":
            return formula
        case _:
            return None


def parseToCNF(parse: list[lp.Formula]):
    if not well_formed_formula(parse):
        return None
    return CNF(NNF(IMPL_FREE(parse[0])))


def to_latex(formula: lp.Formula):
    FORM = form(formula)
    match FORM:
        case "NEGATION":
            return f"(\\neg {to_latex(formula[1])})"
        case "CONJUNCTION":
            return f"({to_latex(formula[0])}) \\wedge ({to_latex(formula[2])})"
        case "DISJUNCTION":
            return f"{to_latex(formula[0])} \\vee {to_latex(formula[2])}"
        case "IMPLIES":
            return f"({to_latex(formula[0])} \\rightarrow {to_latex(formula[2])})"
        case "ATOM":
            return f"{formula}"
        case _:
            return None
