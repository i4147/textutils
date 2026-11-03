from __future__ import annotations

import typing as ty
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field
from qtpy.QtCore import QPoint, QRect, QSize, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QKeyEvent, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap
from qtpy.QtWidgets import (
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import qtextra.helpers as hp
from qtextra.config import QtStyler
from qtextra.widgets.qt_dialog import QtDialog

__all__ = ["QtWelcomeDialog", "WelcomeListItem", "WelcomePage"]


class WelcomeListItem(BaseModel):
    title: str
    description: str = ""
    icon: str = "check"


class WelcomePage(BaseModel):
    title: str
    description: str = ""
    image_path: str | None = None
    items: list[WelcomeListItem] = Field(default_factory=list)
    action_text: str | None = None


class _WelcomeImage(QWidget):
    MAXIMUM_SIZE = QSize(420, 130)

    def __init__(self, pixmap: QPixmap, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = pixmap
        self.setObjectName("qtWelcomeImage")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMaximumHeight(self.MAXIMUM_SIZE.height())

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        if self._pixmap.isNull() or width <= 0:
            return 0
        bounded_width = min(width, self.MAXIMUM_SIZE.width())
        height = round(bounded_width * self._pixmap.height() / self._pixmap.width())
        return min(height, self.MAXIMUM_SIZE.height())

    def sizeHint(self) -> QSize:
        if self._pixmap.isNull():
            return QSize()
        return self._pixmap.size().scaled(
            self.MAXIMUM_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        if self._pixmap.isNull():
            return
        target_size = self._pixmap.size()
        target_size.scale(self.contentsRect().size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRect(QPoint(), target_size)
        target.moveCenter(self.contentsRect().center())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target, self._pixmap)


class _WelcomeListItemWidget(QWidget):
    def __init__(self, item: WelcomeListItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("qtWelcomeListItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.icon_frame = QFrame(self)
        self.icon_frame.setObjectName("qtWelcomeItemIconFrame")
        self.icon_frame.setFixedSize(40, 40)
        icon_layout = hp.make_v_layout(margin=0, parent=self.icon_frame)
        icon_layout.addWidget(
            hp.make_qta_label(self.icon_frame, item.icon, size_preset="small"),
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        text_widget = QWidget(self)
        text_widget.setObjectName("qtWelcomeItemText")
        text_layout = hp.make_v_layout(margin=0, spacing=3, parent=text_widget)
        self.title_label = hp.make_label(
            text_widget,
            item.title,
            bold=True,
            wrap=True,
            object_name="qtWelcomeItemTitle",
            text_format=Qt.TextFormat.PlainText,
        )
        self.description_label = hp.make_label(
            text_widget,
            item.description,
            wrap=True,
            object_name="qtWelcomeItemDescription",
            text_format=Qt.TextFormat.PlainText,
        )
        self.description_label.setVisible(bool(item.description))
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.description_label)

        layout = hp.make_h_layout(margin=0, spacing=18, parent=self)
        layout.addWidget(self.icon_frame, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(text_widget, 1)


class _WelcomeItemList(QWidget):
    def __init__(self, items: ty.Sequence[WelcomeListItem], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("qtWelcomeItemList")
        self._item_widgets = [_WelcomeListItemWidget(item, self) for item in items]
        layout = hp.make_v_layout(margin=0, spacing=8, parent=self)
        for item_widget in self._item_widgets:
            layout.addWidget(item_widget)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        if len(self._item_widgets) < 2:
            return
        color = QColor(QtStyler.foreground())
        color.setAlpha(190)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        for current, following in zip(self._item_widgets, self._item_widgets[1:], strict=False):
            current_frame = current.icon_frame.geometry()
            following_frame = following.icon_frame.geometry()
            x = current.x() + current_frame.center().x()
            top = current.y() + current_frame.bottom()
            bottom = following.y() + following_frame.top()
            painter.drawLine(x, top, x, bottom)


class _WelcomePageWidget(QWidget):
    def __init__(self, page: WelcomePage, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.page = page
        self.setObjectName("qtWelcomePage")
        self.image_widget: _WelcomeImage | None = None
        self.item_list: _WelcomeItemList | None = None
        self._build()

    def _build(self) -> None:
        outer_layout = hp.make_h_layout(margin=0, spacing=0, parent=self)
        outer_layout.addStretch(1)

        content = QWidget(self)
        content.setObjectName("qtWelcomePageContent")
        content.setMinimumWidth(600)
        content.setMaximumWidth(720)
        layout = hp.make_v_layout(margin=(24, 18, 24, 20), spacing=8, parent=content)

        pixmap = self._load_image()
        if pixmap is not None:
            self.image_widget = _WelcomeImage(pixmap, content)
            layout.addWidget(self.image_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
            layout.addSpacing(10)

        self.title_label = hp.make_label(
            content,
            self.page.title,
            wrap=True,
            bold=True,
            font_size=22,
            alignment=Qt.AlignmentFlag.AlignHCenter,
            object_name="qtWelcomePageTitle",
            text_format=Qt.TextFormat.PlainText,
        )
        self.description_label = hp.make_label(
            content,
            self.page.description,
            wrap=True,
            alignment=Qt.AlignmentFlag.AlignHCenter,
            object_name="qtWelcomePageDescription",
            text_format=Qt.TextFormat.PlainText,
        )
        self.description_label.setVisible(bool(self.page.description))
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)

        if self.page.items:
            layout.addSpacing(10)
            self.item_list = _WelcomeItemList(self.page.items, content)
            layout.addWidget(self.item_list)
        layout.addStretch(1)

        outer_layout.addWidget(content, 1)
        outer_layout.addStretch(1)

    def _load_image(self) -> QPixmap | None:
        if not self.page.image_path:
            return None
        path = Path(self.page.image_path).expanduser()
        if not path.is_file():
            logger.warning(f"Welcome page image does not exist: {path}")
            return None
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logger.warning(f"Welcome page image could not be loaded: {path}")
            return None
        return pixmap


class _WelcomeStepIndicator(QWidget):
    DOT_RADIUS = 5
    SPACING = 18

    def __init__(self, count: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._count = max(0, count)
        self._current_index = 0
        self.setFixedHeight(20)
        self.setMinimumWidth(max(20, self._indicator_width()))

    @property
    def count(self) -> int:
        return self._count

    @property
    def current_index(self) -> int:
        return self._current_index

    def set_current_index(self, index: int) -> None:
        self._current_index = max(0, min(index, max(0, self._count - 1)))
        self.update()

    def _indicator_width(self) -> int:
        if not self._count:
            return 0
        return (self._count - 1) * self.SPACING + self.DOT_RADIUS * 2

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        if not self._count:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        start_x = (self.width() - self._indicator_width()) // 2 + self.DOT_RADIUS
        center_y = self.height() // 2
        for index in range(self._count):
            if index < self._current_index:
                color = QtStyler.success()
            elif index == self._current_index:
                color = QtStyler.secondary()
            else:
                color = QColor(QtStyler.foreground())
                color.setAlpha(105)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            center = QPoint(start_x + index * self.SPACING, center_y)
            painter.drawEllipse(center, self.DOT_RADIUS, self.DOT_RADIUS)


class _WelcomeHeader(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_offset: QPoint | None = None
        self.setObjectName("qtWelcomeHeader")

    @staticmethod
    def _global_position(event: QMouseEvent) -> QPoint:
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = self._global_position(event) - self.window().frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(self._global_position(event) - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class QtWelcomeDialog(QtDialog):
    evt_current_changed = Signal(int)
    evt_skipped = Signal()
    evt_finished = Signal()

    def __init__(
        self,
        pages: ty.Sequence[WelcomePage | dict[str, ty.Any]],
        parent: QWidget | None = None,
        *,
        title: str = "Welcome",
        back_text: str = "Back",
        skip_text: str = "Skip intro",
        continue_text: str = "Continue",
        finish_text: str = "Let's go",
        show_skip: bool = True,
    ) -> None:
        materialized = [page if isinstance(page, WelcomePage) else WelcomePage.model_validate(page) for page in pages]
        if not materialized:
            raise ValueError("At least one welcome page is required.")

        self._pages = materialized
        self._current_index = 0
        self._header_title = title
        self._back_text = back_text
        self._skip_text = skip_text
        self._continue_text = continue_text
        self._finish_text = finish_text
        self._show_skip = show_skip

        super().__init__(parent, title=title)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(720, 520)
        self.resize(940, 680)
        self._update_ui()

    @property
    def pages(self) -> tuple[WelcomePage, ...]:
        return tuple(self._pages)

    @property
    def current_index(self) -> int:
        return self._current_index

    def make_panel(self) -> QVBoxLayout:
        root = hp.make_v_layout(margin=8, spacing=0)
        self.frame = QFrame(self)
        self.frame.setObjectName("qtWelcomeFrame")
        self.frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        frame_layout = hp.make_v_layout(margin=0, spacing=0, parent=self.frame)

        self.header = _WelcomeHeader(self.frame)
        header_layout = hp.make_h_layout(margin=(30, 20, 20, 20), spacing=12, parent=self.header)
        self.header_title_label = hp.make_label(
            self.header,
            self._header_title,
            bold=True,
            font_size=18,
            object_name="qtWelcomeHeaderTitle",
            text_format=Qt.TextFormat.PlainText,
        )
        self.step_count_label = hp.make_label(
            self.header,
            "",
            object_name="qtWelcomeStepCount",
            text_format=Qt.TextFormat.PlainText,
        )
        self.step_indicator = _WelcomeStepIndicator(len(self._pages), self.header)
        self.close_button = hp.make_qta_btn(
            self.header,
            "cross",
            tooltip="Close",
            size_preset="normal",
            func=self.reject,
            object_name="qtWelcomeCloseButton",
        )
        self.close_button.setAccessibleName("Close")
        header_layout.addWidget(self.header_title_label)
        header_layout.addWidget(self.step_count_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.step_indicator)
        header_layout.addSpacing(24)
        header_layout.addWidget(self.close_button)
        frame_layout.addWidget(self.header)
        frame_layout.addWidget(hp.make_h_line(self.frame))

        self.stack = QStackedWidget(self.frame)
        self.stack.setObjectName("qtWelcomeStack")
        for page in self._pages:
            scroll = QScrollArea(self.stack)
            scroll.setObjectName("qtWelcomeScroll")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(_WelcomePageWidget(page, scroll))
            self.stack.addWidget(scroll)
        frame_layout.addWidget(self.stack, 1)
        frame_layout.addWidget(hp.make_h_line(self.frame))

        footer = QFrame(self.frame)
        footer.setObjectName("qtWelcomeFooter")
        footer_layout = QGridLayout(footer)
        footer_layout.setContentsMargins(30, 20, 30, 20)
        footer_layout.setHorizontalSpacing(12)
        footer_layout.setColumnStretch(0, 1)
        footer_layout.setColumnStretch(1, 1)
        footer_layout.setColumnStretch(2, 1)

        self.back_button = hp.make_btn(
            footer,
            self._back_text,
            func=self.previous_page,
            bold=True,
            object_name="qtWelcomeBackButton",
        )
        self.skip_button = hp.make_btn(
            footer,
            self._skip_text,
            func=self._on_skip,
            bold=True,
            object_name="qtWelcomeSkipButton",
        )
        self.primary_button = hp.make_btn(
            footer,
            self._continue_text,
            func=self.next_page,
            bold=True,
            object_name="qtWelcomePrimaryButton",
        )
        self.primary_button.setDefault(True)
        footer_layout.addWidget(self.back_button, 0, 0, Qt.AlignmentFlag.AlignLeft)
        footer_layout.addWidget(self.skip_button, 0, 1, Qt.AlignmentFlag.AlignHCenter)
        footer_layout.addWidget(self.primary_button, 0, 2, Qt.AlignmentFlag.AlignRight)
        frame_layout.addWidget(footer)

        root.addWidget(self.frame)
        return root

    def set_current_index(self, index: int) -> None:
        clamped = max(0, min(index, len(self._pages) - 1))
        changed = clamped != self._current_index
        self._current_index = clamped
        self.stack.setCurrentIndex(clamped)
        self._update_ui()
        if changed:
            self.evt_current_changed.emit(clamped)

    def previous_page(self) -> None:
        if self._current_index > 0:
            self.set_current_index(self._current_index - 1)

    def next_page(self) -> None:
        if self._current_index < len(self._pages) - 1:
            self.set_current_index(self._current_index + 1)
            return
        self.evt_finished.emit()
        self.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageDown):
            self.next_page()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            self.previous_page()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.next_page()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)

    def _update_ui(self) -> None:
        total = len(self._pages)
        page = self._pages[self._current_index]
        is_last = self._current_index == total - 1
        self.step_count_label.setText(f"\u00b7 {self._current_index + 1} of {total}")
        self.step_indicator.set_current_index(self._current_index)
        self.back_button.setEnabled(self._current_index > 0)
        self.skip_button.setVisible(self._show_skip and not is_last)
        default_action = self._finish_text if is_last else self._continue_text
        self.primary_button.setText(page.action_text or default_action)

    def _on_skip(self) -> None:
        self.evt_skipped.emit()
        self.accept()
