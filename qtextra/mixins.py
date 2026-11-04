from __future__ import annotations

import typing as ty
from contextlib import contextmanager
from functools import partial
from pathlib import Path

from koyo.timer import MeasureTimer
from loguru import logger
from qtpy.QtCore import QTimer, Signal
from qtpy.QtGui import QCloseEvent, QDragEnterEvent, QDragLeaveEvent, QDropEvent
from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

import qtextra.helpers as hp
from qtextra.config import EVENTS, get_settings
from qtextra.utils.utilities import check_url, get_docs_path

DOC_DIR = Path(get_docs_path())


class DocumentationMixin:
    DOC_HTML_LINK: str = ""

    parent: ty.Callable[..., QWidget]

    ENABLE_TUTORIAL: bool = False
    _docs_tutorial_btn: QPushButton | None = None

    ENABLE_HTML: bool = True
    _docs_info_btn: QPushButton | None = None

    def _make_info_layout(
        self,
        align_right: bool = True,
        html_link: str = "",
        parent: QWidget | None = None,
    ) -> ty.Tuple[QPushButton, QHBoxLayout]:
        if not html_link:
            html_link = self.DOC_HTML_LINK

        self._docs_tutorial_btn = hp.make_qta_btn(
            parent if parent is not None else self.parent(),
            "tutorial",
            tooltip="Click here to launch tutorial for this panel...",
            func=self._open_tutorial,
            hide=not self.ENABLE_TUTORIAL,
        )
        self._docs_info_btn = info_btn = hp.make_qta_btn(
            parent if parent is not None else self.parent(),
            "help",
            tooltip="Click here to see more information about this panel...",
            func=partial(self._open_info_link, html_link),
            hide=not self.ENABLE_HTML,
        )

        layout = QHBoxLayout()
        layout.addWidget(self._docs_tutorial_btn)
        layout.addWidget(self._docs_info_btn)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        if align_right:
            layout.insertSpacerItem(0, hp.make_h_spacer())
        else:
            layout.addSpacerItem(hp.make_h_spacer())
        return info_btn, layout

    def _open_tutorial(self) -> None:
        pass

    @staticmethod
    def _open_info_link(html_link: str) -> None:
        if html_link.startswith("docs/"):
            html_link = (DOC_DIR / html_link).as_uri()

        if html_link.startswith("file:///") or check_url(html_link):
            EVENTS.evt_help_request.emit(html_link)
        else:
            EVENTS.evt_msg_warning.emit("The provided link is not valid")


class ConfigMixin:
    _initialized_config: bool = False
    _is_setting_config: bool = False

    @contextmanager
    def setting_config(self) -> ty.Generator[None, None, None]:
        self._is_setting_config = True
        try:
            yield
        finally:
            self._is_setting_config = False

    def on_set_from_config(self) -> None:
        with self.setting_config():
            self._on_set_from_config(get_settings())
        self._initialized_config = True

    def _on_set_from_config(self, settings: ty.Any | None = None) -> None:
        pass


class TimerMixin:
    def _add_periodic_timer(self, interval: int, fcn: ty.Callable | None, start: bool = True) -> QTimer:
        timer = QTimer(self)
        timer.setInterval(interval)
        if fcn:
            timer.timeout.connect(fcn)

        if start:
            timer.start()
        logger.debug(f"Added periodic timer event that runs every {interval / 1000}s")
        return timer

    def _add_single_shot_timer(self, delay: int, fcn: ty.Callable) -> QTimer:
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(delay)
        timer.timeout.connect(fcn)
        timer.start()
        return timer

    @contextmanager
    def measure_time(
        self,
        message: str = "Task took",
        func: ty.Callable = logger.trace,
    ) -> ty.Generator[None, None, None]:
        with MeasureTimer() as timer:
            yield
        func(f"{message} {timer()}")


class MinimizeMixin:
    _make_move_handle: ty.Callable[..., ty.Any]
    hide: ty.Callable[..., ty.Any]
    clearFocus: ty.Callable[..., ty.Any]

    def _make_hide_handle(self) -> tuple[QPushButton, QHBoxLayout]:
        hide_btn = hp.make_qta_btn(
            self,
            "minimise",
            tooltip="Click here to minimize the popup window",
        )
        hide_btn.clicked.connect(self.on_hide)

        hide_layout = self._make_move_handle()
        hide_layout.addWidget(hide_btn)
        return hide_btn, hide_layout

    def on_hide(self) -> None:
        self.hide()
        self.clearFocus()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.on_hide()
        event.ignore()


class CloseMixin:
    HIDE_WHEN_CLOSE: bool = False
    _title_label: QLabel

    close: ty.Callable[..., ty.Any]
    _make_move_handle: ty.Callable[..., ty.Any]
    _close_handle = None

    def _make_close_layout(self, title: str = "") -> QHBoxLayout:
        return self._make_close_handle(title=title)[1]

    def _make_close_handle(self, title: str = "") -> tuple[QPushButton, QHBoxLayout]:
        self._close_handle = hp.make_qta_btn(
            self,
            "cross",
            tooltip="Click here to close the popup window",
            size_preset="normal",
            func=self.close,
        )

        close_layout = self._make_move_handle()
        close_layout.addWidget(self._close_handle)
        self._title_label.setText(title)
        return self._close_handle, close_layout

    def _make_hide_layout(self, title: str = "") -> QHBoxLayout:
        return self._make_hide_handle(title=title)[1]

    def _make_hide_handle(self, title: str = "") -> tuple[QPushButton, QHBoxLayout]:
        self.HIDE_WHEN_CLOSE = True
        return self._make_close_handle(title)


class IndicatorMixin:
    evt_indicate = Signal(str)
    evt_indicate_about = Signal(str, str)

    def on_toast(self, title: str, message: str, func: ty.Callable = logger.info) -> None:
        from qtextra.widgets.qt_toast import QtToast

        func(message)
        QtToast(self).show_message(title, message)

    @staticmethod
    def on_notify_info(msg: str, func: ty.Callable = logger.info) -> None:
        EVENTS.evt_msg_info.emit(msg)
        func(msg)

    @staticmethod
    def on_notify_success(msg: str, func: ty.Callable = logger.success) -> None:
        EVENTS.evt_msg_success.emit(msg)
        func(msg)

    @staticmethod
    def on_notify_warning(msg: str, func: ty.Callable = logger.warning) -> None:
        EVENTS.evt_msg_warning.emit(msg)
        func(msg)

    @staticmethod
    def on_notify_error(msg: str, func: ty.Callable = logger.error) -> None:
        EVENTS.evt_msg_error.emit(msg)
        func(msg)

    @staticmethod
    def on_notify_critical(msg: str, func: ty.Callable = logger.critical) -> None:
        EVENTS.evt_msg_critical.emit(msg)
        func(msg)

    @staticmethod
    def on_notification_info(content: str, title: str = "Info", func: ty.Callable = logger.info) -> None:
        EVENTS.evt_notification_info.emit(title, content)
        func(content)

    @staticmethod
    def on_notification_success(content: str, title: str = "Success", func: ty.Callable = logger.success) -> None:
        EVENTS.evt_notification_success.emit(title, content)
        func(content)

    @staticmethod
    def on_notification_warning(content: str, title: str = "Warning", func: ty.Callable = logger.warning) -> None:
        EVENTS.evt_notification_warning.emit(title, content)
        func(content)

    @staticmethod
    def on_notification_error(content: str, title: str = "Error", func: ty.Callable = logger.error) -> None:
        EVENTS.evt_notification_error.emit(title, content)
        func(content)

    @staticmethod
    def on_notification_critical(
        content: str, title: str = "Critical error", func: ty.Callable = logger.critical
    ) -> None:
        EVENTS.evt_notification_critical.emit(title, content)
        func(content)

    def _indicate_success(self, source: str | None = None) -> None:
        pass
        # if source and isinstance(source, str):
        #     self.evt_indicate_about.emit("success", source)
        # else:
        #     self.evt_indicate.emit("success")

    def _indicate_success_any(self, *_args: ty.Any, **_kwargs: ty.Any) -> None:
        self._indicate_success()

    def _indicate_failure(self, source: str | None = None) -> None:
        pass
        # if source:
        #     self.evt_indicate_about.emit("warning", source)
        # else:
        #     self.evt_indicate.emit("warning")


class DragAndDropMixin:
    centralWidget: ty.Callable[..., QWidget]

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        hp.toast(
            self,
            "Drag & drop",
            "Drop the files in the app and we will try to open them..",
            icon="info",
            position="top_left",
        )
        hp.update_property(self.centralWidget(), "drag", True)
        hp.call_later(self, self._clear_drag_property, 2000)
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        hp.update_property(self.centralWidget(), "drag", False)

    def dropEvent(self, event: QDropEvent) -> None:
        hp.update_property(self.centralWidget(), "drag", False)
        self._handle_drop(event)

    def _handle_drop(self, event: QDropEvent) -> None:
        raise NotImplementedError("Must implement method")

    def _clear_drag_property(self) -> None:
        hp.update_property(self.centralWidget(), "drag", False)
