from __future__ import annotations

import typing as ty

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox, QSizePolicy, QWidget

import qtextra.helpers as hp


class QtRemovableComboBox(QWidget):
    evt_removed = Signal(object)
    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        items: ty.Sequence[str] | None = None,
        tooltip: str = "",
        remove_tooltip: str = "Remove",
    ):
        super().__init__(parent)
        self.combobox = QComboBox(self)
        self.combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if tooltip:
            self.combobox.setToolTip(tooltip)
        if items:
            self.combobox.addItems(items)

        self.remove_btn = hp.make_qta_btn(
            self,
            "delete",
            tooltip=remove_tooltip,
            size_preset="small",
            func=self._on_remove,
        )

        layout = hp.make_h_layout(parent=self, margin=0, spacing=1)
        layout.addWidget(self.combobox, 1)
        layout.addWidget(self.remove_btn, 0)

        self.combobox.currentIndexChanged.connect(self.currentIndexChanged)
        self.combobox.currentTextChanged.connect(self.currentTextChanged)

    def _on_remove(self) -> None:
        self.evt_removed.emit(self)
        self.hide()

    def addItem(self, *args: ty.Any) -> None:
        self.combobox.addItem(*args)

    def addItems(self, items: ty.Sequence[str]) -> None:
        self.combobox.addItems(items)

    def removeItem(self, index: int) -> None:
        self.combobox.removeItem(index)

    def currentIndex(self) -> int:
        return self.combobox.currentIndex()

    def setCurrentIndex(self, index: int) -> None:
        self.combobox.setCurrentIndex(index)

    def currentText(self) -> str:
        return self.combobox.currentText()

    def setCurrentText(self, text: str) -> None:
        self.combobox.setCurrentText(text)

    def currentData(self, role: int = 256) -> ty.Any:
        return self.combobox.currentData(role)

    def count(self) -> int:
        return self.combobox.count()

    def clear(self) -> None:
        self.combobox.clear()

    def setEditable(self, editable: bool) -> None:
        self.combobox.setEditable(editable)

    def itemText(self, index: int) -> str:
        return self.combobox.itemText(index)

    def itemData(self, index: int, role: int = 256) -> ty.Any:
        return self.combobox.itemData(index, role)

    def setItemText(self, index: int, text: str) -> None:
        self.combobox.setItemText(index, text)

    def setItemData(self, index: int, value: ty.Any, role: int = 256) -> None:
        self.combobox.setItemData(index, value, role)

    def findText(self, text: str) -> int:
        return self.combobox.findText(text)


if __name__ == "__main__":
    import sys

    from qtextra.utils.dev import qframe

    app, frame, ha = qframe(False)

    def _removed(widget: QtRemovableComboBox) -> None:
        ha.removeWidget(widget)
        widget.deleteLater()

    for i in range(3):
        combo = QtRemovableComboBox(items=["Option A", "Option B", "Option C"])
        combo.setCurrentIndex(i)
        combo.evt_removed.connect(_removed)
        ha.addWidget(combo)

    frame.show()
    sys.exit(app.exec_())
