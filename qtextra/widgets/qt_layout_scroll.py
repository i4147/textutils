from __future__ import annotations

import typing as ty

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QResizeEvent, QShowEvent
from qtpy.QtWidgets import QHBoxLayout, QLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

import qtextra.helpers as hp


class QtScrollableLayoutWidget(QScrollArea):
    MIN_HEIGHT: int = 30

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._widget = QWidget()
        self._main_layout = self._make_layout()
        self.setWidgetResizable(True)
        self.setWidget(self._widget)
        self.setContentsMargins(0, 0, 0, 0)

    def _make_layout(self) -> QHBoxLayout | QVBoxLayout:
        raise NotImplementedError("Must implement method")

    def count(self) -> int:
        return self._main_layout.count()

    def get_widget(self, index: int) -> QWidget | None:
        item = self._main_layout.itemAt(index)
        if not item:
            return None
        return item.widget()

    def setSpacing(self, spacing: int) -> None:
        self._main_layout.setSpacing(spacing)

    def addWidget(self, widget: QWidget, **kwargs: ty.Any) -> None:
        self._main_layout.addWidget(widget, **kwargs)
        self._update_scroll()

    def insertWidget(self, index: int, widget: QWidget, **kwargs: ty.Any) -> None:
        self._main_layout.insertWidget(index, widget, **kwargs)
        self._update_scroll()

    def addLayout(self, layout: QLayout, **kwargs: ty.Any) -> None:
        self._main_layout.addLayout(layout, **kwargs)
        self._update_scroll()

    def insertLayout(self, index: int, layout: QLayout, **kwargs: ty.Any) -> None:
        self._main_layout.insertLayout(index, layout, **kwargs)
        self._update_scroll()

    def removeWidget(self, widget: QWidget) -> None:
        index = self._main_layout.indexOf(widget)
        if index != -1:
            self.removeWidgetOrLayout(index)

    def removeWidgetOrLayout(self, index: int) -> None:
        widget = self.get_widget(index)
        if widget:
            self._main_layout.removeWidget(widget)
            widget.deleteLater()
            self._update_scroll()

    def minimum_height_for_widgets(self) -> int:
        height = 0
        for i in range(self.count()):
            widget = self.get_widget(i)
            if widget:
                height = max(
                    height, widget.sizeHint().height(), widget.minimumSizeHint().height(), widget.minimumHeight()
                )
        return height

    def minimum_width_for_widgets(self) -> int:
        height = 0
        for i in range(self.count()):
            widget = self.get_widget(i)
            if widget:
                height = max(height, widget.sizeHint().width(), widget.minimumSizeHint().width(), widget.minimumWidth())
        return height

    def _content_size_hint(self) -> QSize:
        return self._widget.sizeHint().expandedTo(self._widget.minimumSizeHint()).expandedTo(self._widget.minimumSize())

    def set_min_height(self, min_height: int) -> None:
        self.MIN_HEIGHT = min_height
        self._update_scroll()

    def _update_scroll(self) -> None:
        pass

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._update_scroll()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_scroll()


class QtScrollableHLayoutWidget(QtScrollableLayoutWidget):
    MIN_HEIGHT: int = 30

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

    def _make_layout(self) -> QHBoxLayout:
        return hp.make_h_layout(stretch_after=True, spacing=1, margin=1, parent=self._widget)

    def set_min_height(self, min_height: int) -> None:
        self.MIN_HEIGHT = min_height
        self._update_scroll()

    def _update_scroll(self) -> None:
        height = self.MIN_HEIGHT
        if self.count() > 0:
            height = max(height, self.minimum_height_for_widgets(), self._content_size_hint().height())

        available_width = max(0, self.viewport().width())
        needs_h_scroll = self._content_size_hint().width() > available_width > 0
        scroll_height = self.horizontalScrollBar().sizeHint().height() if needs_h_scroll else 0

        target_height = height + (self.frameWidth() * 2) + scroll_height
        if self.minimumHeight() != target_height:
            self.setMinimumHeight(target_height)
        if self.maximumHeight() != target_height:
            self.setMaximumHeight(target_height)


class QtScrollableVLayoutWidget(QtScrollableLayoutWidget):
    MIN_WIDTH: int = 30

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

    def _make_layout(self) -> QHBoxLayout:
        return hp.make_v_layout(stretch_after=True, spacing=1, margin=1, parent=self._widget)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QPushButton

    from qtextra.utils.dev import qframe

    random_text = ["Short", "Longer", "Different text", "More text", "Even longer button text"] * 4

    app, frame, ha = qframe(horz=False)
    layout = QtScrollableHLayoutWidget(None)
    ha.addWidget(layout)
    for text in random_text:
        layout.addWidget(QPushButton(text))

    layout = QtScrollableVLayoutWidget(None)
    ha.addWidget(layout)
    for text in random_text:
        layout.addWidget(QPushButton(text))
    frame.show()
    sys.exit(app.exec_())
