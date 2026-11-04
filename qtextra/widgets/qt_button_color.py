from __future__ import annotations

import typing as ty

import numpy as np
from koyo.color import ColorType, rgbs_to_hex
from koyo.color import transform_color as _transform_color
from qtpy.QtCore import QEvent, QRectF, QSize, Qt, Signal, Slot
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import QAbstractButton, QColorDialog, QFrame, QPushButton, QWidget

BASE_COLOR = "#FFFFFF"
AnyColorType = ty.Union[ColorType, QColor]
TRANSPARENT = np.array([0, 0, 0, 0], np.float32)


FILL_QSS = """
    QPushButton#color_btn {
        border: none;
        margin: 0px;
        padding: 0px;
        background-color: COLOR;
    }
"""
EMPTY_QSS = FILL_QSS.replace("COLOR", "transparent")
HOVER_QSS = """
    QPushButton#color_btn:hover {
        border: 2px solid black;
    }
"""


class QtColorButton(QPushButton):
    evt_color_changed: Signal = Signal(str)

    def __init__(self, *args, color=None, size: ty.Tuple[int, int] = (16, 16), **kwargs):
        self._color = color

        super().__init__(*args, **kwargs)

        self.setFixedSize(QSize(*size))
        self.setObjectName("color_btn")
        self.pressed.connect(self.onColorPicker)

        if self._color is not None:
            self.setColor(self._color)

    @property
    def color(self):
        return self._color

    def setColor(self, color):
        if not hasattr(self, "_color"):
            return

        if color != self._color:
            self._color = color
            self.evt_color_changed.emit(color)

        if self._color:
            self.setStyleSheet(FILL_QSS.replace("COLOR", self._color) + HOVER_QSS)
        else:
            self.setStyleSheet(EMPTY_QSS + HOVER_QSS)

    def onColorPicker(self):
        color = QColor(self._color) if self._color is not None else None
        dlg = QColorDialog(color, parent=self)
        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.setColor(None)

        return super().mousePressEvent(e)


class QtColorSwatch(QFrame):
    evt_color_changed = Signal(np.ndarray)

    def __init__(
        self,
        parent: QWidget | None = None,
        tooltip: str | None = None,
        initial_color: ColorType | None = None,
        add_frame: bool = True,
    ):
        super().__init__(parent)
        self.setObjectName("colorSwatch")
        self.setToolTip(tooltip or "Click to set color")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._initial_color = initial_color
        self._color: np.ndarray = TRANSPARENT
        self.evt_color_changed.connect(self._update_swatch_style)
        if initial_color is not None:
            self.set_color(initial_color)
        if add_frame:
            self.setFrameShape(QFrame.Shape.Box)
            self.setLineWidth(2)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)

    @property
    def color(self) -> np.ndarray:
        return self._color

    @property
    def hex_color(self) -> str:
        return rgbs_to_hex(self._color)[0]

    @property
    def hex_color_no_alpha(self) -> str:
        return rgbs_to_hex(self._color)[0][0:7]

    @Slot(np.ndarray)
    def _update_swatch_style(self, _color: ColorType) -> None:
        rgb = [int(x * 255) for x in self._color[:3]]
        alpha = int(self._color[3] * 255) if len(self._color) > 3 else 255
        rgba = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
        brightness = (0.299 * rgb[0]) + (0.587 * rgb[1]) + (0.114 * rgb[2])
        border = "rgba(20, 20, 20, 160)" if brightness > 186 else "rgba(255, 255, 255, 180)"
        self.setStyleSheet(
            f"#colorSwatch {{background-color: {rgba};border: 1px solid {border};border-radius: 3px;}}",
        )

    def mouseReleaseEvent(self, event: QEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            from qtextra.helpers import get_color

            initial = QColor(*(255 * self._color).astype("int"))
            color = get_color(self, initial, False)
            if color is not None:
                self.set_color(color)

    def set_color(self, color: AnyColorType, force: bool = False) -> None:
        if isinstance(color, QColor):
            _color = (np.array(color.getRgb()) / 255).astype(np.float32)
        else:
            try:
                from napari.utils.colormaps.standardize_color import transform_color

                _color = transform_color(color)[0]
            except ValueError:
                return self.evt_color_changed.emit(self._color)
            except ImportError:
                try:
                    _color = _transform_color(color)[0]
                except ValueError:
                    return self.evt_color_changed.emit(self._color)

        emit = np.any(self._color != _color)
        self._color = _color
        if emit or np.all(_color == TRANSPARENT):
            self.evt_color_changed.emit(_color)
        if force:
            self._update_swatch_style(_color)
            return None
        return None

    hexColor = hex_color
    setColor = set_color


class ColorCircleButton(QAbstractButton):
    colorChanged = Signal(QColor)

    def __init__(
        self,
        color: QColor | str = "#4db8ff",
        diameter: int = 32,
        selected: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._color = QColor(color)
        self._diameter = diameter
        self._selected = selected
        self._hovered = False

        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(self.sizeHint())

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    @property
    def color(self) -> QColor:
        return QColor(self._color)

    def set_color(self, color: QColor | str) -> None:
        self._color = QColor(color)
        self.update()

    @property
    def selected(self) -> bool:
        return self._selected

    def set_selected(self, value: bool) -> None:
        self._selected = value
        self.update()

    def sizeHint(self) -> QSize:
        pad = 6
        s = self._diameter + pad * 2
        return QSize(s, s)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = self._diameter / 2

        if self._selected:
            ring_r = r + 3
            p.setPen(QPen(QColor("white"), 2.5, Qt.PenStyle.SolidLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2))

        fill = QColor(self._color)
        if self._hovered:
            fill = fill.lighter(115)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill))
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_color_dialog()
        super().mousePressEvent(event)

    def _open_color_dialog(self):
        new_color = QColorDialog.getColor(
            self._color,
            self,
            "Pick a color",
            QColorDialog.ShowAlphaChannel,
        )
        if new_color.isValid():
            self._color = new_color
            self.update()
            self.colorChanged.emit(QColor(self._color))

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)


if __name__ == "__main__":
    import sys

    from qtextra.utils.dev import qframe

    app, frame, ha = qframe(False)
    frame.setLayout(ha)
    frame.setMinimumSize(400, 400)

    w = QtColorButton(size=(64, 64), color="#FF00FF")
    ha.addWidget(w)
    ww = QtColorSwatch(initial_color="#FF0000")
    ha.addWidget(ww)
    ww = QtColorSwatch(initial_color="#FFFF00")
    ha.addWidget(ww)
    ww = QtColorSwatch(initial_color=(255, 123, 32))
    ha.addWidget(ww)

    buttons: list[ColorCircleButton] = []

    def _on_color_changed(btn: ColorCircleButton, color: QColor):
        for b in buttons:
            b.set_selected(b is btn)
        print(f"Color picked: {color.name(QColor.HexArgb)}")

    def _make_color_changed_handler(btn: ColorCircleButton):
        def _handle_color_changed(color: QColor) -> None:
            _on_color_changed(btn, color)

        return _handle_color_changed

    for i, hex_color in enumerate(["#4db8ff", "#4db8ff", "#4db8ff", "#2a6ebb", "#22264b", "#b3a0d6"]):
        btn = ColorCircleButton(color=hex_color, diameter=32)
        btn.set_selected(i == 1)
        btn.colorChanged.connect(_make_color_changed_handler(btn))
        ha.addWidget(btn)
        buttons.append(btn)

    frame.show()
    sys.exit(app.exec_())
