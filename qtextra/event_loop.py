from __future__ import annotations

import os
import sys
from warnings import warn

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication

from qtextra import __version__

APP_ID: str = os.getenv("QTEXTRA_APP_ID", f"qtextra.qtextra.{__version__}")
APP_NAME: str = os.getenv("QTEXTRA_APP_NAME", "qtextra")
APP_ORG_NAME: str = os.getenv("QTEXTRA_APP_ORG_NAME", "qtextra")
APP_ORG_DOMAIN: str = os.getenv("QTEXTRA_APP_ORG_DOMAIN", "")


_app_ref = None


def set_app_id(app_id):
    if os.name == "nt" and app_id and not getattr(sys, "frozen", False):
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


_defaults = {
    "app_name": APP_NAME,
    "app_version": __version__,
    "org_name": APP_ORG_NAME,
    "org_domain": APP_ORG_DOMAIN,
    "app_id": APP_ID,
}


def get_app(
    *,
    app_name: str | None = None,
    app_version: str | None = None,
    icon: str | None = None,
    org_name: str | None = None,
    org_domain: str | None = None,
    app_id: str | None = None,
) -> QApplication:
    set_values = {k for k, v in locals().items() if v}
    kwargs = locals() if set_values else _defaults
    global _app_ref

    app = QApplication.instance()
    if app:
        set_values.discard("ipy_interactive")
        if set_values:
            warn(
                f"QApplication already existed, these arguments to to 'get_app' were ignored: {set_values}",
                stacklevel=2,
            )
    else:
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        if hasattr(Qt, "AA_UseStyleSheetPropagationInWidgetStyles"):
            QApplication.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
        if hasattr(Qt, "AA_ShareOpenGLContexts"):
            QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
        app = QApplication(sys.argv)

    app.setApplicationName(kwargs.get("app_name"))
    app.setApplicationVersion(kwargs.get("app_version"))
    app.setOrganizationName(kwargs.get("org_name"))
    app.setOrganizationDomain(kwargs.get("org_domain"))
    app.setWindowIcon(QIcon(kwargs.get("icon")))
    set_app_id(kwargs.get("app_id"))

    # if perf_config and not perf_config.patched:
    #     # Will patch based on config file.
    #     perf_config.patch_callables()

    # if not _ipython_has_eventloop():
    #     NOTIFICATION_MANAGER.notification_ready.connect(QtNotification.show_notification)
    # NOTIFICATION_MANAGER.notification_ready.connect(show_console_notification)

    if app.windowIcon().isNull():
        app.setWindowIcon(QIcon(kwargs.get("icon")))

    if not _app_ref:
        from qtpy.QtCore import QDir

        from qtextra.config import THEMES

        # app.aboutToQuit.connect(wait_for_workers_to_quit)
        for name in THEMES.themes:
            QDir.addSearchPath(f"theme_{name}", str(THEMES.get_theme_path(name)))

    _app_ref = app
    return app


def _ipython_has_eventloop() -> bool:
    try:
        from IPython import get_ipython

        return get_ipython().active_eventloop == "qt"
    except (ImportError, AttributeError):
        return False


def run(*, force=False, max_loop_level=1, _func_name="run"):
    # from ionglow.utils.notifications import NOTIFICATION_MANAGER

    from qtextra.dialogs.sentry import install_error_monitor

    if _ipython_has_eventloop():
        return

    app = QApplication.instance()
    if not app:
        raise RuntimeError(
            "No Qt app has been created. One can be created by calling `get_app()` or qtpy.QtWidgets.QApplication([])",
        )
    if not app.topLevelWidgets() and not force:
        warn(
            "Refusing to run a QApplication with no topLevelWidgets. "
            f"To run the app anyway, use `{_func_name}(force=True)`",
            stacklevel=2,
        )
        return

    if app.thread().loopLevel() >= max_loop_level:
        loops = app.thread().loopLevel()
        s = "s" if loops > 1 else ""
        warn(
            f"A QApplication is already running with {loops} event loop{s}."
            "To enter *another* event loop, use "
            f"`{_func_name}(max_loop_level={loops + 1})`",
            stacklevel=2,
        )
        return
    install_error_monitor()
    app.exec_()
