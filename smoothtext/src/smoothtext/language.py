from __future__ import annotations
from enum import Enum

_Constants: dict[any, tuple[str, str, str]] = {}


class Language(Enum):
    English = "English"
    German = "German"
    Turkish = "Turkish"

    English_GB = "English (Great Britain)"
    English_US = "English (United States)"

    German_DE = "German (Germany)"

    Turkish_TR = "Turkish (Türkiye)"

    def family(self) -> Language:
        if self in [Language.English_GB, Language.English_US]:
            return Language.English

        if self in [Language.German_DE]:
            return Language.German

        if self in [Language.Turkish_TR]:
            return Language.Turkish

        return self

    def variants(self) -> list[Language]:
        if self.family() == Language.English:
            return [Language.English_GB, Language.English_US]

        if self.family() == Language.German:
            return [Language.German_DE]

        if self.family() == Language.Turkish:
            return [Language.Turkish_TR]

        return [self]

    def alpha2(self) -> str:
        return _Constants[self][1][:2]

    def alpha3(self) -> str:
        return _Constants[self][2][:3]

    def readability_formulas(self) -> list["ReadabilityFormula"]:
        from . import ReadabilityFormula

        if Language.English == self.family():
            return [
                ReadabilityFormula.Automated_Readability_Index,
                ReadabilityFormula.Flesch_Reading_Ease,
                ReadabilityFormula.Flesch_Kincaid_Grade,
                ReadabilityFormula.Flesch_Kincaid_Grade_Simplified,
            ]

        if Language.German == self.family():
            return [
                ReadabilityFormula.Flesch_Reading_Ease,
                ReadabilityFormula.Wiener_Sachtextformel,
                ReadabilityFormula.Wiener_Sachtextformel_1,
                ReadabilityFormula.Wiener_Sachtextformel_2,
                ReadabilityFormula.Wiener_Sachtextformel_3,
                ReadabilityFormula.Wiener_Sachtextformel_4,
            ]

        if Language.Turkish == self.family():
            return [
                ReadabilityFormula.Atesman,
                ReadabilityFormula.Bezirci_Yilmaz,
            ]

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, value: Language | str) -> bool:
        if isinstance(value, Language):
            return self is value

        if isinstance(value, str):
            return self == Language.parse(value)

        return False

    @staticmethod
    def families() -> list[Language]:
        return [Language.English, Language.German, Language.Turkish]

    @staticmethod
    def values() -> list[Language]:
        return [
            Language.English,
            Language.English_GB,
            Language.English_US,
            Language.German,
            Language.German_DE,
            Language.Turkish,
            Language.Turkish_TR,
        ]

    @staticmethod
    def parse(language: Language | str) -> Language | None:
        if isinstance(language, Language):
            return language

        if not isinstance(language, str):
            return None

        language = language.lower()

        if "_" in language:
            language = language.replace("_", "-")

        for k, v in _Constants.items():
            for e in v:
                if e == language:
                    if k == k.family():
                        return k.variants()[-1]

                    return k

        return None

    @staticmethod
    def parse_multiple(
        languages: Language | str | list[Language | str],
    ) -> list[Language]:
        if isinstance(languages, Language):
            return [languages]

        if isinstance(languages, str):
            languages = [s.strip() for s in languages.split(",")]

        return list({pl for l in languages if (pl := Language.parse(l)) is not None})


_Constants[Language.English] = (Language.English.value.lower(), "en", "eng")
_Constants[Language.English_GB] = (Language.English_GB.value.lower(), "en-gb", "eng-gb")
_Constants[Language.English_US] = (Language.English_US.value.lower(), "en-us", "eng-us")

_Constants[Language.German] = (Language.German.value.lower(), "de", "deu")
_Constants[Language.German_DE] = (Language.German_DE.value.lower(), "de-de", "deu-de")

_Constants[Language.Turkish] = (Language.Turkish.value.lower(), "tr", "tur")
_Constants[Language.Turkish_TR] = (Language.Turkish_TR.value.lower(), "tr-tr", "tur-tr")
