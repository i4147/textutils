from __future__ import annotations

import typing as ty
from pathlib import Path

from pydantic import BaseModel
from qtpy.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from qtpy.QtGui import (
    QBrush,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QShowEvent,
)
from qtpy.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import qtextra.helpers as hp
from qtextra.config import QtStyler


class ShowcasePage(BaseModel):
    title: str
    description: str = ""
    image_path: str | None = None
    link_text: str = ""
    link_url: str = ""


class _ShowcaseImage(QWidget):
    _CORNER_RADIUS = 10.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_image(self, path: str | None) -> None:
        self._pixmap = QPixmap(path) if path and Path(path).is_file() else QPixmap()
        self.update()

    def _scaled_image_rect(self) -> QRect:
        if self._pixmap.isNull():
            return self.rect()
        size = self._pixmap.size()
        size.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRect(QPoint(), size)
        rect.moveCenter(self.rect().center())
        return rect

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        frame_rect = QRectF(self.rect().adjusted(0, 0, -1, -1))
        clip_path = QPainterPath()
        clip_path.addRoundedRect(frame_rect, self._CORNER_RADIUS, self._CORNER_RADIUS)
        painter.setClipPath(clip_path)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QtStyler.background())
        gradient.setColorAt(1.0, QtStyler.foreground())
        painter.fillPath(clip_path, gradient)

        if not self._pixmap.isNull():
            painter.drawPixmap(self._scaled_image_rect(), self._pixmap)


class _ShowcaseDots(QWidget):
    evt_clicked = Signal(int)

    _DOT_RADIUS = 4
    _ACTIVE_RADIUS = 6
    _SPACING = 18

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._count = 0
        self._current_index = 0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(18)

    @property
    def count(self) -> int:
        return self._count

    @property
    def current_index(self) -> int:
        return self._current_index

    def set_count(self, count: int) -> None:
        self._count = max(0, count)
        self._current_index = min(self._current_index, max(0, self._count - 1))
        self.setMinimumWidth(max(24, self._indicator_width()))
        self.updateGeometry()
        self.update()

    def set_current_index(self, index: int) -> None:
        if self._count:
            self._current_index = max(0, min(index, self._count - 1))
        else:
            self._current_index = 0
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(max(24, self._indicator_width()), 18)

    def _indicator_width(self) -> int:
        if not self._count:
            return 0
        return (self._count - 1) * self._SPACING + self._ACTIVE_RADIUS * 2

    def _first_center_x(self) -> int:
        return (self.width() - self._indicator_width()) // 2 + self._ACTIVE_RADIUS

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            first_x = self._first_center_x()
            for index in range(self._count):
                if abs(event.position().x() - (first_x + index * self._SPACING)) <= self._ACTIVE_RADIUS + 3:
                    self.evt_clicked.emit(index)
                    event.accept()
                    return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._count:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        first_x = self._first_center_x()
        center_y = self.height() // 2
        for index in range(self._count):
            center = QPoint(first_x + index * self._SPACING, center_y)
            if index == self._current_index:
                painter.setBrush(QBrush(QtStyler.highlight()))
                painter.setPen(QPen(QtStyler.highlight(), 1))
                painter.drawEllipse(center, self._ACTIVE_RADIUS, self._ACTIVE_RADIUS)
            else:
                painter.setBrush(QBrush(QtStyler.foreground()))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, self._DOT_RADIUS, self._DOT_RADIUS)


class _ShowcaseOverlay(QFrame):
    evt_link_activated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("QtShowcaseOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "#QtShowcaseOverlay { background-color: rgba(0, 0, 0, 175); border-radius: 10px; }"
            "#QtShowcaseOverlay QLabel { background: transparent; color: white; }"
            "#QtShowcaseOverlay QPushButton { background: transparent; color: white; border: none;"
            " text-align: left; text-decoration: underline; padding: 0; }"
        )

        self.title_label = hp.make_label(self, "", bold=True, wrap=True, font_size=18)
        self.description_label = hp.make_label(self, "", wrap=True)
        self.link_btn = hp.make_btn(self, "", func=self._on_link)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(4)
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.link_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self._link_url = ""

    def set_page(self, page: ShowcasePage) -> None:
        self.title_label.setText(page.title)
        self.description_label.setText(page.description)
        self.description_label.setVisible(bool(page.description))
        self.link_btn.setText(page.link_text)
        self._link_url = page.link_url
        self.link_btn.setVisible(bool(page.link_text and page.link_url))

    def _on_link(self) -> None:
        if self._link_url:
            self.evt_link_activated.emit(self._link_url)


class QtShowcaseWidget(QWidget):
    evt_current_changed = Signal(int)
    evt_link_activated = Signal(str)

    def __init__(
        self,
        pages: ty.Sequence[ShowcasePage | dict[str, ty.Any]] | None = None,
        interval_ms: int = 30_000,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pages: list[ShowcasePage] = []
        self._current_index = -1
        self._animation: ty.Any | None = None

        self._image = _ShowcaseImage(self)
        self._overlay = _ShowcaseOverlay(self)
        self._overlay.evt_link_activated.connect(self.evt_link_activated)
        self._dots = _ShowcaseDots(self)
        self._dots.evt_clicked.connect(self._on_dot_clicked)

        content = QWidget(self)
        content_layout = QGridLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 4)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._image, 0, 0)
        content_layout.addWidget(self._overlay, 0, 0, alignment=Qt.AlignmentFlag.AlignBottom)

        self._previous_btn = hp.make_qta_btn(
            self,
            "previous",
            tooltip="Show previous page.",
            func=self._on_previous,
            size_preset="large",
        )
        self._next_btn = hp.make_qta_btn(
            self,
            "next",
            tooltip="Show next page.",
            func=self._on_next,
            size_preset="large",
        )

        canvas = QWidget(self)
        canvas_layout = QGridLayout(canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(content, 0, 0)
        canvas_layout.addWidget(self._previous_btn, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        canvas_layout.addWidget(self._next_btn, 0, 0, alignment=Qt.AlignmentFlag.AlignRight)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(2)
        root_layout.addWidget(canvas, stretch=1)
        root_layout.addWidget(self._dots, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._timer = QTimer(self)
        self._timer.setInterval(max(1, interval_ms))
        self._timer.timeout.connect(self.next_page)
        self.set_pages(pages or [])

    @property
    def pages(self) -> tuple[ShowcasePage, ...]:
        return tuple(self._pages)

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def interval_ms(self) -> int:
        return self._timer.interval()

    def set_pages(self, pages: ty.Sequence[ShowcasePage | dict[str, ty.Any]]) -> None:
        self._pages = [page if isinstance(page, ShowcasePage) else ShowcasePage.model_validate(page) for page in pages]
        self._current_index = 0 if self._pages else -1
        self._update_navigation()
        self._render_current(animate=False)
        self._restart_timer()

    def set_current_index(self, index: int, *, animate: bool = True) -> None:
        if not 0 <= index < len(self._pages) or index == self._current_index:
            return
        self._current_index = index
        self._render_current(animate=animate)
        self.evt_current_changed.emit(index)

    def next_page(self) -> None:
        if len(self._pages) > 1:
            self.set_current_index((self._current_index + 1) % len(self._pages))

    def previous_page(self) -> None:
        if len(self._pages) > 1:
            self.set_current_index((self._current_index - 1) % len(self._pages))

    def _on_next(self) -> None:
        self.next_page()
        self._restart_timer()

    def _on_previous(self) -> None:
        self.previous_page()
        self._restart_timer()

    def _on_dot_clicked(self, index: int) -> None:
        self.set_current_index(index)
        self._restart_timer()

    def _render_current(self, *, animate: bool) -> None:
        page = (
            self._pages[self._current_index]
            if self._current_index >= 0
            else ShowcasePage(title="No highlights available")
        )
        self._image.set_image(page.image_path)
        self._overlay.set_page(page)
        self._dots.set_current_index(self._current_index)

        if animate:
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setStartValue(0.25)
            animation.setEndValue(1.0)
            animation.setDuration(180)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animation = animation
            animation.start()

    def _update_navigation(self) -> None:
        visible = len(self._pages) > 1
        self._previous_btn.setVisible(visible)
        self._next_btn.setVisible(visible)
        self._dots.set_count(len(self._pages))
        self._dots.setVisible(visible)

    def _restart_timer(self) -> None:
        self._timer.stop()
        if self.isVisible() and len(self._pages) > 1:
            self._timer.start()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._restart_timer()

    def hideEvent(self, event: QEvent) -> None:
        self._timer.stop()
        super().hideEvent(event)
