from __future__ import annotations

import typing as ty

from qtpy.QtCore import QSize, Qt, Signal
from qtpy.QtWidgets import QFrame, QHBoxLayout, QPushButton, QSizePolicy, QWidget

import qtextra.helpers as hp

if ty.TYPE_CHECKING:
    from qtextra.typing import QtaSizePreset
    from qtextra.widgets.qt_button_icon import QtImagePushButton
    from qtextra.widgets.qt_separator import QtVertLine


class QtSegmentedButton(QFrame):
    evt_clicked = Signal()

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        *,
        flat: bool = False,
        tooltip: str = "",
        func: ty.Callable | list[ty.Callable] | None = None,
    ):
        super().__init__(parent=parent)
        self._actions: list[QtImagePushButton] = []
        self._separators: list[QWidget] = []

        self.button = QPushButton(text, self)
        self.button.setObjectName("mainButton")
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.button.clicked.connect(self.evt_clicked)
        if func:
            [self.button.clicked.connect(f) for f in hp._validate_func(func)]
        self.button.setToolTip(tooltip)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.button, stretch=1)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        if flat:
            self.set_flat(True)

    def add_action(
        self,
        icon_name: str,
        tooltip: str = "",
        func: ty.Callable | list[ty.Callable] | None = None,
        *,
        size_preset: QtaSizePreset = "average",
        hide: bool = False,
    ) -> tuple[QtImagePushButton, QtVertLine]:
        sep = hp.make_v_line(self, hide=hide)
        self._layout.addWidget(sep)
        self._separators.append(sep)

        btn = hp.make_qta_btn(
            self,
            icon_name,
            tooltip=tooltip,
            size_preset=size_preset,
            func=func,
            hide=hide,
        )
        btn.setProperty("transparent", True)

        self._layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self._actions.append(btn)
        return btn, sep

    @property
    def text(self) -> str:
        return self.button.text()

    def setText(self, text: str) -> None:
        self.button.setText(text)

    def setEnabled(self, enabled: bool) -> None:
        self.button.setEnabled(enabled)
        for btn in self._actions:
            btn.setEnabled(enabled)

    def set_flat(self, flat: bool) -> None:
        self.setProperty("flat", str(flat).lower())
        hp.polish_widget(self)

    def sizeHint(self) -> QSize:
        w = self.button.sizeHint().width()
        h = self.button.sizeHint().height()
        for btn in self._actions:
            bh = btn.sizeHint()
            w += bh.width()
            h = max(h, bh.height())
        w += len(self._separators)
        margins = self.contentsMargins()
        w += margins.left() + margins.right()
        h += margins.top() + margins.bottom()
        return QSize(w, h)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()


if __name__ == "__main__":

    def _main() -> None:
        import sys

        from qtextra.utils.dev import qframe

        app, frame, va = qframe(False)
        frame.setMinimumSize(500, 200)

        btn1 = QtSegmentedButton("Run pipeline", frame)
        btn1.evt_clicked.connect(lambda: print("Run clicked"))
        btn1.add_action("settings", "Configure", lambda: print("Settings clicked"))
        btn1.add_action("close", "Cancel", lambda: print("Cancel clicked"))
        va.addWidget(btn1)

        btn2 = QtSegmentedButton("Export", frame)
        btn2.evt_clicked.connect(lambda: print("Export clicked"))
        btn2.add_action("save", "Save to file", lambda: print("Save clicked"))
        btn2.add_action("copy", "Copy to clipboard", lambda: print("Copy clicked"))
        btn2.add_action("delete", "Discard", lambda: print("Discard clicked"))
        va.addWidget(btn2)

        btn3 = QtSegmentedButton("Flat button", frame, flat=True)
        btn3.evt_clicked.connect(lambda: print("Flat clicked"))
        btn3.add_action("add", "Add item", lambda: print("Add clicked"))
        va.addWidget(btn3)

        btn4 = QtSegmentedButton("No actions", frame)
        btn4.evt_clicked.connect(lambda: print("No-action clicked"))
        va.addWidget(btn4)

        frame.show()
        sys.exit(app.exec_())

    _main()
