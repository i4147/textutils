from PyQt6.Qsci import QsciLexer, QsciAPIs
from PyQt6.QtGui import QIcon
from typing import Optional


class LanguageBase:
    def getLexer(self) -> QsciLexer:
        return None

    def getName(self) -> str:
        return "Unknown"

    def getExtensions(self) -> list[str]:
        return []

    def getStarttext(self) -> list[str]:
        return []

    def getMimeType(self) -> list[str]:
        return []

    def getID(self) -> str:
        return "unknown"

    def getAPI(self, lexer: QsciLexer) -> Optional[QsciAPIs]:
        return None

    def getIcon(self) -> Optional[QIcon]:
        return None
