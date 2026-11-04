from __future__ import annotations

import typing as ty
from contextlib import suppress

from qtpy.QtCore import QEvent, QSize, Qt
from qtpy.QtGui import QColor, QFont, QFontMetrics, QPainter, QPaintEvent
from qtpy.QtWidgets import QWidget

from qtextra.config import THEMES
from qtextra.widgets.qt_overlay import QtOverlay

BadgeState = ty.Literal["", "info", "success", "warning", "error"]
BadgeMode = ty.Literal["dot", "count"]
BadgeSize = ty.Literal["xs", "sm", "md", "lg", "xl"]


class QtNotificationBadge(QtOverlay):
    STATES: ty.ClassVar[tuple[BadgeState, ...]] = ("", "info", "success", "warning", "error")
    MODES: ty.ClassVar[tuple[BadgeMode, ...]] = ("dot", "count")
    SIZES: ty.ClassVar[tuple[BadgeSize, ...]] = ("xs", "sm", "md", "lg", "xl")
    SIZE_MAP: ty.ClassVar[dict[BadgeSize, int]] = {
        "xs": 10,
        "sm": 12,
        "md": 16,
        "lg": 20,
        "xl": 24,
    }
    STATE_COLOR_KEYS: ty.ClassVar[dict[BadgeState, str]] = {
        "info": "info",
        "success": "success",
        "warning": "warning",
        "error": "error",
    }
    MAX_COUNT: ty.ClassVar[int] = 99
    Y_OFFSET: ty.ClassVar[int] = 0

    def __init__(
        self,
        parent: QWidget | None = None,
        widget: QWidget | None = None,
        state: BadgeState = "error",
        mode: BadgeMode = "dot",
        size: BadgeSize = "md",
        count: int | None = None,
        visible_when_zero: bool = False,
        auto_clear_on_click: bool = False,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
    ):
        super().__init__(parent=parent, alignment=alignment)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self._state: BadgeState = "error"
        self._mode: BadgeMode = "dot"
        self._size: BadgeSize = "md"
        self._count = 0
        self._visible_when_zero = bool(visible_when_zero)
        self._auto_clear_on_click = bool(auto_clear_on_click)
        self._clear_target: QWidget | None = None

        with suppress(RuntimeError):
            THEMES.evt_theme_changed.connect(self._on_theme_changed)

        self.set_state(state)
        self.set_mode(mode)
        self.set_badge_size(size)
        self.set_count(count)
        if widget is not None:
            self.attach_to(widget)
        else:
            self._sync_visibility()

    @property
    def state(self) -> BadgeState:
        return self._state

    def set_state(self, state: BadgeState) -> None:
        if state not in self.STATES:
            raise ValueError(f"Invalid state: {state}. Must be one of {self.STATES}")
        self._state = state
        self._sync_visibility()
        self.update()

    def clear(self) -> None:
        self.set_state("")

    @property
    def mode(self) -> BadgeMode:
        return self._mode

    def set_mode(self, mode: BadgeMode) -> None:
        if mode not in self.MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self.MODES}")
        self._mode = mode
        self.updateGeometry()
        self._relayout()
        self._sync_visibility()
        self.update()

    @property
    def badge_size(self) -> BadgeSize:
        return self._size

    def set_badge_size(self, size: BadgeSize) -> None:
        if size not in self.SIZES:
            raise ValueError(f"Invalid size: {size}. Must be one of {self.SIZES}")
        self._size = size
        diameter = self._diameter
        self.setMinimumSize(QSize(diameter, diameter))
        self.updateGeometry()
        self._relayout()
        self._sync_visibility()
        self.update()

    @property
    def count(self) -> int:
        return self._count

    def set_count(self, count: int | None) -> None:
        if count is None:
            count = 0
        if count < 0:
            raise ValueError("Badge count must be >= 0")
        self._count = int(count)
        self.updateGeometry()
        self._relayout()
        self._sync_visibility()
        self.update()

    def set_visible_when_zero(self, visible: bool) -> None:
        self._visible_when_zero = bool(visible)
        self._sync_visibility()

    def set_auto_clear_on_click(self, state: bool) -> None:
        self._auto_clear_on_click = bool(state)
        self._update_clear_target()

    def attach_to(self, widget: QWidget | None) -> None:
        if widget is not None and self.parentWidget() is None:
            self.setParent(widget.window())
        self.set_widget(widget)
        self._update_clear_target()
        self._sync_visibility()

    def eventFilter(self, recv, event):
        if (
            recv is self._clear_target
            and self._auto_clear_on_click
            and event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self.clear()
        return super().eventFilter(recv, event)

    def sizeHint(self) -> QSize:
        diameter = self._diameter
        text = self._display_text
        if self._mode == "dot" or not text:
            return QSize(diameter, diameter)
        metrics = QFontMetrics(self._badge_font())
        height = max(diameter, metrics.height() + 2)
        width = max(height, metrics.horizontalAdvance(text) + max(6, height // 2))
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        color = QColor(self._background_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(self.rect(), self.height() / 2, self.height() / 2)

        text = self._display_text
        if self._mode == "count" and text:
            painter.setPen(QColor(self._text_color))
            painter.setFont(self._badge_font())
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

        painter.end()
        del event

    @property
    def _diameter(self) -> int:
        return self.SIZE_MAP[self._size]

    @property
    def _display_text(self) -> str:
        if self._mode != "count":
            return ""
        if self._count <= 0 and not self._visible_when_zero:
            return ""
        return f"{self.MAX_COUNT}+" if self._count > self.MAX_COUNT else str(self._count)

    @property
    def _background_color(self) -> str:
        return THEMES.get_hex_color(self.STATE_COLOR_KEYS[self._state])

    @property
    def _text_color(self) -> str:
        return THEMES.get_text_color_for_background(self._background_color)

    def _badge_font(self) -> QFont:
        font = QFont(self.font())
        font.setBold(True)
        font.setPointSizeF(max(10.0, self._diameter * 0.82))
        return font

    def _sync_visibility(self) -> None:
        should_show = (
            self._anchor_is_visible()
            and bool(self._state)
            and (self._mode == "dot" or self._count > 0 or self._visible_when_zero)
        )
        self.setVisible(should_show)

    def _sync_to_anchor(self) -> None:
        self._sync_visibility()

    def _anchor_is_visible(self) -> bool:
        widget = self.widget()
        if widget is None:
            return False
        window = self.window()
        if window is None or window is widget:
            return widget.isVisible()
        return widget.isVisible() and window.isVisible() and widget.isVisibleTo(window)

    def _on_theme_changed(self) -> None:
        self.update()

    def _update_clear_target(self) -> None:
        widget = self.widget()
        if self._clear_target is widget:
            return
        if self._clear_target is not None:
            self._clear_target.removeEventFilter(self)
        self._clear_target = widget
        if self._clear_target is not None and self._auto_clear_on_click:
            self._clear_target.installEventFilter(self)
