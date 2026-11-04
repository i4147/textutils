import contextlib

from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexers import get_lexer_by_name
from qtpy import QtGui


def get_text_char_format(style: dict[str, str]) -> QtGui.QTextCharFormat:
    text_char_format = QtGui.QTextCharFormat()
    try:
        text_char_format.setFontFamilies(["monospace"])
    except AttributeError:
        text_char_format.setFontFamily("monospace")
    if style.get("color"):
        text_char_format.setForeground(QtGui.QColor(f"#{style['color']}"))

    if style.get("bgcolor"):
        text_char_format.setBackground(QtGui.QColor(style["bgcolor"]))

    if style.get("bold"):
        text_char_format.setFontWeight(QtGui.QFont.Bold)
    if style.get("italic"):
        text_char_format.setFontItalic(True)
    if style.get("underline"):
        text_char_format.setFontUnderline(True)

    return text_char_format


class QFormatter(Formatter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data = []
        self._style = {name: get_text_char_format(style) for name, style in self.style}

    def format(self, tokensource, outfile):
        self.data = []

        for token, value in tokensource:
            self.data.extend(
                [
                    self._style[token],
                ]
                * len(value),
            )


class Codelighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent, theme: str, lang: str = "python") -> None:
        super().__init__(parent)
        self.formatter = QFormatter(style=theme)
        self.lexer = get_lexer_by_name(lang)

    def highlightBlock(self, text):
        cb = self.currentBlock()
        p = cb.position()
        text = self.document().toPlainText() + "\n"
        highlight(text, self.lexer, self.formatter)

        for i in range(len(text)):
            with contextlib.suppress(IndexError):
                self.setFormat(i, 1, self.formatter.data[p + i])
