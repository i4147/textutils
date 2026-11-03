import typing as ty

from loguru import logger
from qtpy.QtCore import QObject, Signal

try:
    from qtextra.utils.notifications import Notification
except ImportError:
    Notification = object


class Events(QObject):
    """Events emitter."""

    evt_help_request = Signal(str)

    evt_msg_info = Signal(str)
    evt_msg_success = Signal(str)
    evt_msg_warning = Signal(str)
    evt_msg_error = Signal(str)
    evt_msg_critical = Signal(str)

    evt_notification_popup = Signal(str, str, str)
    evt_notification_long_popup = Signal(str, str, str)
    evt_notification_info = Signal(str, str)
    evt_notification_success = Signal(str, str)
    evt_notification_warning = Signal(str, str)
    evt_notification_error = Signal(str, str)
    evt_notification_critical = Signal(str, str)

    evt_exception = Signal(tuple)

    evt_notification_action = Signal(str, tuple)
    evt_notification_dismiss = Signal()
    evt_notification = Signal(Notification)

    evt_splash_msg = Signal(str)
    evt_splash_close = Signal()

    evt_statusbar_help = Signal(object)
    evt_statusbar_status = Signal(object)

    evt_force_exit = Signal()

    def emit_evt_statusbar_status(self, obj):
        """Emit statusbar status event."""
        self.evt_statusbar_status.emit(obj)

    def emit_evt_statusbar_help(self, obj):
        """Emit statusbar help event."""
        self.evt_statusbar_help.emit(obj)

    def on_notification_info(self, content: str, title: str = "Info", func: ty.Callable = logger.info) -> None:
        """Notify the user of an info."""
        self.evt_notification_info.emit(title, content)
        func(content)

    def on_notification_success(self, content: str, title: str = "Success", func: ty.Callable = logger.success) -> None:
        """Notify the user of an success."""
        self.evt_notification_success.emit(title, content)
        func(content)

    def on_notification_warning(self, content: str, title: str = "Warning", func: ty.Callable = logger.warning) -> None:
        """Notify the user of a warning."""
        self.evt_notification_warning.emit(title, content)
        func(content)

    def on_notification_error(self, content: str, title: str = "Error", func: ty.Callable = logger.error) -> None:
        """Notify the user of an error."""
        self.evt_notification_error.emit(title, content)
        func(content)

    def on_notification_critical(
        self,
        content: str,
        title: str = "Critical error",
        func: ty.Callable = logger.critical,
    ) -> None:
        """Notify the user of an error."""
        self.evt_notification_critical.emit(title, content)
        func(content)


EVENTS: Events = Events()
