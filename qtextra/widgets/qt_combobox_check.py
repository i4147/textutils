import typing as ty
from functools import partial

from qtpy.QtCore import QModelIndex, Qt, Signal
from qtpy.QtGui import QStandardItemModel
from qtpy.QtWidgets import QComboBox

from qtextra.helpers import call_later, qt_signals_blocked


class CheckableAbstractModel(QStandardItemModel):
    evt_checked = Signal(int, bool)

    def setData(self, index: QModelIndex, value: ty.Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.CheckStateRole:
            # self.evt_checked.emit(index.row(), not value)
            call_later(self, partial(self.evt_checked.emit, index.row(), not value), delay=50)
        elif role == Qt.ItemDataRole.DisplayRole:
            pass
        return super().setData(index, value, role)


class QtCheckableComboBox(QComboBox):
    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)
        self.setModel(CheckableAbstractModel(self))
        self.evt_checked = self.model().evt_checked

    def addItem(self, item: str, data: ty.Any = None):
        super().addItem(item, data)
        item = self.model().item(self.count() - 1, 0)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(Qt.CheckState.Unchecked)

    def addItems(self, texts: ty.Sequence[str]) -> None:
        current = self.count()
        super().addItems(texts)
        for index in range(current, self.count()):
            item = self.model().item(index, 0)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked)

    def itemChecked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == Qt.CheckState.Checked

    def setItemChecked(self, index: int, checked: bool) -> bool:
        item = self.model().item(index, 0)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def get_checked(self) -> ty.List[int]:
        return [index for index in range(self.count()) if self.itemChecked(index)]

    def checked_texts(self) -> ty.List[str]:
        return [self.itemText(index) for index in self.get_checked()]

    def checked_data(self):
        return [self.itemData(index) for index in self.get_checked()]

    def set_checked_texts(self, texts: ty.List[str]):
        with qt_signals_blocked(self):
            [self.setItemChecked(index, False) for index in range(self.count())]
            for text in texts:
                index = self.findText(text)
                if index != -1:
                    self.setItemChecked(index, True)

    checkedData = checked_data
    checkedTexts = checked_texts
    getChecked = get_checked
    setCheckedTexts = set_checked_texts


if __name__ == "__main__":
    import sys

    from qtextra.utils.dev import qframe

    app, frame, ha = qframe(False)
    frame.setLayout(ha)
    frame.setMinimumSize(400, 400)

    wdg = QtCheckableComboBox()
    wdg.addItems(["Option 1", "Option 2", "Option 3"])
    ha.addWidget(wdg)

    frame.show()
    sys.exit(app.exec_())
