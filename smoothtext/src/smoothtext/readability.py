from . import Language

from enum import Enum


class ReadabilityFormula(Enum):
    Automated_Readability_Index = "Automated Readability Index"
    Flesch_Reading_Ease = "Flesch Reading Ease"
    Flesch_Kincaid_Grade = "Flesch-Kincaid Grade"
    Flesch_Kincaid_Grade_Simplified = "Flesch-Kincaid Grade Simplified"

    Wiener_Sachtextformel = "Wiener Sachtextformel"
    Wiener_Sachtextformel_1 = "Wiener Sachtextformel 1"
    Wiener_Sachtextformel_2 = "Wiener Sachtextformel 2"
    Wiener_Sachtextformel_3 = "Wiener Sachtextformel 3"
    Wiener_Sachtextformel_4 = "Wiener Sachtextformel 4"

    Atesman = "Ateşman"
    Bezirci_Yilmaz = "Bezirci-Yılmaz"

    def supports(self, language: "Language") -> bool:
        from . import Language

        if not isinstance(language, Language):
            return False

        return self in language.readability_formulas()
