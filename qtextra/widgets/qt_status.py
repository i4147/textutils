"""Status bar widgets.

Taken and modified from spyder.widgets.status
"""

from __future__ import annotations

from qtpy.QtCore import Qt, QTimer, Signal
from qtpy.QtGui import QFont, QIcon, QMouseEvent
from qtpy.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QStatusBar, QWidget

import qtextra.helpers as hp
from qtextra.widgets.qt_button_tool import QtToolButton
from qtextra.widgets.qt_label_icon import QtQtaLabel, QtQtaNotificationLabel


class QtStatusbarLabel(QLabel):
    """Statusbar 