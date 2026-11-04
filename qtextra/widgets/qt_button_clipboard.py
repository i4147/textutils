from __future__ import annotations

from qtpy.QtGui import QGuiApplication, QImage
from qtpy.QtWidgets import QLabel, QTextEdit, QWidget

from qtextra.config import EVENTS, THEMES
from qtextra.widgets.qt_button_icon import QtImagePushButton


def copy_text_to_clipboard(text: str):
    cb = QGuiApplication.clipboard()
    cb.setText(text)
    EVENTS.evt_msg_success.emit("Copied text to clipboard!")


def copy_image_to_clipboard(image: QImage):
    cb = QGuiApplication.clipboard()
    cb.setImage(image)
    EVENTS.evt_msg_success.emit("Copied image to clipboard!")


class QtCopyToClipboardButton(QtImagePushButton):
    def __init__(self, text_edit: QLabel | QTextEdit, parent: QWidget | None = None):
        super().__init__(parent)
        # self.setObjectName("QtCopyToClipboardButton")
        self.text_edit = text_edit
        self.setToolTip("Copy to clipboard")
        self.set_qta("copy_to_clipboard")
        self.clicked.connect(self.copy_to_clipboard)

    def text_to_copy(self) -> str:
        if hasattr(self.text_edit, "toPlainText"):
            return str(self.text_edit.toPlainText())
        if hasattr(self.text_edit, "text"):
            return self.text_edit.text()
        return ""

    def copy_to_clipboard(self) -> None:
        from qtextra.helpers import add_flash_animation

        copy_text_to_clipboard(self.text_to_copy())
        add_flash_animation(self.text_edit, color=THEMES.get_hex_color("foreground"), duration=500)

    copyToClipboard = copy_to_clipboard
