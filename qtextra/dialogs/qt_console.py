from __future__ import annotations

import re
import sys
import typing as ty

from ipykernel.inprocess.ipkernel import InProcessInteractiveShell
from ipykernel.zmqshell import ZMQInteractiveShell
from IPython import get_ipython
from IPython.terminal.interactiveshell import TerminalInteractiveShell
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from qtextra.widgets.qt_dialog import QtFramelessTool


def _noop_push(_variables: ty.Any) -> None:
    """Fallback push callable when an embedded console is unavailable."""


def str_to_rgb(arg):
    """Convert an rgb string 'rgb(x,y,z)' to a list of ints [x,y,z]."""
    return list(map(int, re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", arg).groups()))


if sys.platform.startswith("win"):
    import asyncio

    try:
        from asyncio import WindowsProactorEventLoopPolicy, WindowsSelectorEventLoopPolicy
    except ImportError:
        pass
    else:
        if type(asyncio.get_event_loop_policy()) is WindowsProactorEventLoopPolicy:
            asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


class QtConsole(RichJupyterWidget):
    """Qt view for the console, an integrated iPython terminal in napari.

    Parameters
    ----------
    variables : dict, optional
        Dictionary of variables to add to the console namespace.

    Attributes
    ----------
    kernel_client : qtconsole.inprocess.QtInProcessKernelClient,
                    qtconsole.client.QtKernelClient, or None
        Client for the kernel if it exists, None otherwise.
    shell : ipykernel.inprocess.ipkernel.InProcessInteractiveShell,
            ipykernel.zmqshell.ZMQInteractiveShell, or None.
        Shell for the kernel if it exists, None otherwise.
    """

    def __init__(self, variables: dict[str, ty.Any] | None = None):
        super().__init__()
        if variables is None:
            variables = {}

        self.setFocusProxy(self._control)

        shell = get_ipython()

        if shell is None:
            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel(show_banner=False)
            kernel_manager.kernel.gui = "qt"

            kernel_client = kernel_manager.client()
            kernel_client.start_channels()

            self.kernel_manager = kernel_manager
            self.kernel_client = kernel_client
            self.shell = kernel_manager.kernel.shell
            self.push = self.shell.push
        elif isinstance(shell, InProcessInteractiveShell):
            kernel_manager = QtInProcessKernelManager(kernel=shell.kernel)
            kernel_client = kernel_manager.client()

            self.kernel_manager = kernel_manager
            self.kernel_client = kernel_client
            self.shell = kernel_manager.kernel.shell
            self.push = self.shell.push
        elif isinstance(shell, (TerminalInteractiveShell, ZMQInteractiveShell)):
            self.kernel_client = None
            self.kernel_manager = None
            self.shell = None
            self.push = _noop_push

        else:
            raise ValueError(f"ipython shell not recognized; got {type(shell)}")
        self.push(variables)

        self.enable_calltips = False

        self._update_theme()

        # self.execute_on_complete_input = True

    def _update_theme(self, event: ty.Any = None) -> None:
        """Update the napari GUI theme."""
        from qtextra.config.theme import THEMES

        self.style_sheet = THEMES.get_theme_stylesheet()

        # self.style_sheet = get_stylesheet(self.viewer.theme)

        self.syntax_style = THEMES.syntax_style
        bracket_color = QColor(*str_to_rgb(THEMES.get_rgb_color("highlight")))
        self._bracket_matcher.format.setBackground(bracket_color)

    def closeEvent(self, event):
        """Clean up the integrated console in napari."""
        if self.kernel_client is not None:
            self.kernel_client.stop_channels()
        if self.kernel_manager is not None and self.kernel_manager.has_kernel:
            self.kernel_manager.shutdown_kernel()

        self._completion_widget.deleteLater()
        self._call_tip_widget.deleteLater()
        self.deleteLater()
        event.accept()


class QtConsoleDialog(QtFramelessTool):
    """Console popup."""

    HIDE_WHEN_CLOSE = True

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def make_panel(self) -> QFormLayout:
        """Make panel."""
        _, header_layout = self._make_hide_handle()
        self._title_label.setText("IPython Console")

        self._console = QtConsole()

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addWidget(self._console)
        layout.setSpacing(2)
        layout.setContentsMargins(6, 6, 6, 6)
        return layout

    def push_variables(self, variables: dict[str, ty.Any]) -> None:
        """Push variables to console."""
        self._console.push(variables)
