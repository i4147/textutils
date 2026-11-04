from __future__ import annotations

import os
import re
import sys

import qtpy
from qtpy.QtWidgets import QApplication

RICH_TEXT_PATTERN = re.compile("<[^\n]+>")


def _ipython_has_eventloop() -> bool:
    ipy_module = sys.modules.get("IPython")
    if not ipy_module:
        return False

    shell = ipy_module.get_ipython()
    if not shell:
        return False

    return shell.active_eventloop == "qt"


def _pycharm_has_eventloop(app: QApplication) -> bool:
    in_pycharm = "PYCHARM_HOSTED" in os.environ
    in_event_loop = getattr(app, "_in_event_loop", False)
    return in_pycharm and in_event_loop


def qt_might_be_rich_text(text) -> bool:
    if qtpy.PYSIDE2:
        from qtpy.QtGui import Qt as _Qt
    else:
        from qtpy.QtCore import Qt as _Qt

    try:
        return _Qt.mightBeRichText(text)
    except Exception:
        return bool(RICH_TEXT_PATTERN.search(text))
