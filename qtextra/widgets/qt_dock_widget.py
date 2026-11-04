from __future__ import annotations

from functools import reduce
from operator import ior

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDockWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from qtextra.config.events import EVENTS
from qtextra.helpers import qt_signals_blocked


class QtDockedWidget(QDockWidget):
    def __init__(
        self,
        parent,
        widget: QWidget,
        *,
        name: str = "",
        area: str = "bottom",
        allowed_areas: list[str] | None = None,
    ):
        self._parent = parent
        super().__init__(name)
        self.name = name

        areas = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }
        if area not in areas:
            raise ValueError(f"area argument must be in {list(areas.keys())}")
        self.area = area
        self.qt_area = areas[area]

        if allowed_areas:
            if not isinstance(allowed_areas, (list, tuple)):
                raise TypeError("`allowed_areas` must be a list or tuple")
            if not all(area in areas for area in allowed_areas):
                raise ValueError(f"all allowed_areas argument must be in {list(areas.keys())}")
            allowed_areas = reduce(ior, [areas[a] for a in allowed_areas])
        else:
            allowed_areas = Qt.AllDockWidgetAreas
        self.setAllowedAreas(allowed_areas)
        self.setMinimumHeight(50)
        self.setMinimumWidth(50)
        self.setObjectName(name)

        self.setWidget(widget)
        if widget:
            widget.setParent(self)
        self._initial_features = self.features()
        self.dockLocationChanged.connect(self._set_title_orientation)

        self.title = QtCustomTitleBar(self, title=self.name)
        self.setTitleBarWidget(self.title)
        self.visibilityChanged.connect(self._on_visibility_changed)
        EVENTS.evt_splash_msg.emit(f"Setup {name} panel...")

    def keyPressEvent(self, event):
        return self._parent.keyPressEvent(event)

    def _set_title_orientation(self, area):
        if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
            features = self._initial_features
        else:
            features = self._initial_features | self.DockWidgetVerticalTitleBar
        self.setFeatures(features)

    @property
    def is_vertical(self):
        if not self.isFloating():
            par = self._parent
            if par and hasattr(par, "dockWidgetArea"):
                return par.dockWidgetArea(self) in (
                    Qt.LeftDockWidgetArea,
                    Qt.RightDockWidgetArea,
                )
        return self.size().height() > self.size().width()

    def _on_visibility_changed(self, visible):
        if not visible:
            return
        with qt_signals_blocked(self):
            self.setTitleBarWidget(None)
            if not self.isFloating():
                self.title = QtCustomTitleBar(self, title=self.name, vertical=not self.is_vertical)
                self.setTitleBarWidget(self.title)


class QtCustomTitleBar(QLabel):
    def __init__(self, parent, title: str = "", vertical=False):
        super().__init__(parent)
        self.setObjectName("QtCustomTitleBar")
        self.setProperty("vertical", str(vertical))
        self.vertical = vertical
        self.setToolTip("Drag to move or double-click to float")

        line = QFrame(self)
        line.setObjectName("QtCustomTitleBarLine")

        self.close_button = QPushButton(self)
        self.close_button.setToolTip("Hide this panel")
        self.close_button.setObjectName("QtTitleBarCloseButton")
        self.close_button.setCursor(Qt.ArrowCursor)
        self.close_button.clicked.connect(self._toggle_parent_visibility)
        self.float_button = QPushButton(self)
        self.float_button.setToolTip("Float this panel")
        self.float_button.setObjectName("QtTitleBarFloatButton")
        self.float_button.setCursor(Qt.ArrowCursor)
        self.float_button.clicked.connect(self._toggle_parent_floating)
        self.title = QLabel(title, self)
        self.title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum))

        if vertical:
            layout = QVBoxLayout()
            layout.setSpacing(4)
            layout.setContentsMargins(0, 8, 0, 8)
            line.setFixedWidth(1)
            layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(self.float_button, 0, Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(line, 0, Qt.AlignmentFlag.AlignHCenter)
            self.title.hide()

        else:
            layout = QHBoxLayout()
            layout.setSpacing(4)
            layout.setContentsMargins(8, 1, 8, 0)
            line.setFixedHeight(1)
            layout.addWidget(self.close_button)
            layout.addWidget(self.float_button)
            layout.addWidget(line)
            layout.addWidget(self.title)

        self.setLayout(layout)
        self.setCursor(Qt.OpenHandCursor)

    def sizeHint(self):
        szh = super().sizeHint()
        if self.vertical:
            szh.setWidth(20)
        else:
            szh.setHeight(20)
        return szh

    def _toggle_parent_visibility(self) -> None:
        parent = self.parent()
        if parent is not None:
            parent.toggleViewAction().trigger()

    def _toggle_parent_floating(self) -> None:
        parent = self.parent()
        if parent is not None:
            parent.setFloating(not parent.isFloating())
