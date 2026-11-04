from __future__ import annotations

import typing as ty
import warnings
from contextlib import suppress
from copy import deepcopy
from functools import partial

import qtawesome
from qtpy.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from qtpy.QtGui import QBrush, QColor, QEnterEvent, QPainter, QPolygonF
from qtpy.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

import qtextra.helpers as hp
from qtextra.assets import get_icon
from qtextra.config import THEMES
from qtextra.typing import QtaSizePreset
from qtextra.widgets._qta_mixin import QtaMixin
from qtextra.widgets.qt_notification_badge import BadgeMode, BadgeSize, BadgeState, QtNotificationBadge
from qtextra.widgets.qt_tooltip_rich import QtRichToolTip

INDICATOR_TYPES = {"success": "success", "warning": "warning", "active": "progress"}

PRESET_TO_BADGE_SIZE: dict[str, BadgeSize] = {
    "xxsmall": "xs",
    "xsmall": "xs",
    "small": "sm",
    "normal": "md",
    "average": "md",
    "medium": "lg",
    "large": "lg",
    "xlarge": "xl",
    "xxlarge": "xl",
    "xxxlarge": "xl",
}


class QtImagePushButton(QPushButton, QtaMixin):
    evt_click = Signal(QPushButton)
    evt_right_click = Signal(QPushButton)
    count: int = 0
    count_enabled: bool = False
    has_right_click: bool = False
    menu_enabled: bool = False

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        self._icon_color = kwargs.pop("icon_color_override", None)
        self._badge: QtNotificationBadge | None = None
        self._base_button_size: QSize = QSize(20, 20)
        super().__init__()
        self.setFixedSize(20, 20)
        self.setProperty("transparent", False)
        self.transparent = False
        with suppress(RuntimeError):
            THEMES.evt_theme_icon_changed.connect(self._update_qta)

    def set_count(self, count: int, enabled: bool = True) -> None:
        self.count = count
        self.count_enabled = enabled
        badge = self._ensure_badge()
        badge.set_mode("count")
        badge.set_state("info" if enabled else "")
        badge.set_count(count if enabled else 0)
        self._refresh_button_footprint()

    def set_badge(
        self,
        *,
        count: int | None = None,
        state: BadgeState = "info",
        mode: BadgeMode = "count",
        visible_when_zero: bool = False,
    ) -> None:
        badge = self._ensure_badge()
        badge.set_state(state)
        badge.set_mode(mode)
        badge.set_visible_when_zero(visible_when_zero)
        if mode == "count":
            badge.set_count(count if count is not None else self.count)
            if count is not None:
                self.count = count
            self.count_enabled = bool(state)
        self._refresh_button_footprint()

    def clear_badge(self) -> None:
        self.count = 0
        self.count_enabled = False
        if self._badge is not None:
            self._badge.clear()
        self._refresh_button_footprint()

    def _ensure_badge(self) -> QtNotificationBadge:
        if self._badge is None:
            badge = QtNotificationBadge(state="info", mode="count", size=self._preset_to_badge_size())
            badge.attach_to(self)
            self._badge = badge
        else:
            self._badge.set_badge_size(self._preset_to_badge_size())
        return self._badge

    def _preset_to_badge_size(self) -> BadgeSize:
        preset = self.property("qta_size_preset")
        if isinstance(preset, str) and preset in PRESET_TO_BADGE_SIZE:
            return PRESET_TO_BADGE_SIZE[preset]
        height = self._base_button_size.height() or self.height() or self.sizeHint().height()
        if height < 16:
            return "xs"
        if height < 24:
            return "sm"
        if height < 40:
            return "md"
        if height < 80:
            return "lg"
        return "xl"

    def _refresh_button_footprint(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)
        if self._badge is not None:
            self._badge.set_badge_size(self._preset_to_badge_size())
            self._badge._relayout()
            self._badge._sync_visibility()
        self.updateGeometry()

    def setFixedSize(self, *args: ty.Any, **kwargs: ty.Any) -> None:
        if len(args) == 1 and isinstance(args[0], QSize):
            self._base_button_size = QSize(args[0])
        elif len(args) == 2:
            self._base_button_size = QSize(int(args[0]), int(args[1]))
        else:
            super().setFixedSize(*args, **kwargs)
            self._base_button_size = QSize(self.minimumSize())
            self._refresh_button_footprint()
            return
        super().setFixedSize(self._base_button_size)
        self._refresh_button_footprint()

    def _apply_qta_size(
        self,
        widget_size: QSize,
        icon_size: QSize,
        *,
        preset: QtaSizePreset | None = None,
        use_legacy_object_name: bool = False,
    ) -> None:
        self._base_button_size = QSize(widget_size)
        super()._apply_qta_size(
            widget_size,
            icon_size,
            preset=preset,
            use_legacy_object_name=use_legacy_object_name,
        )
        if self._badge is not None:
            self._badge.set_badge_size(self._preset_to_badge_size())
        self._refresh_button_footprint()

    def setText(self, text: str) -> None:
        self.setProperty("with_text", True)
        super().setText(text)

    def set_transparent(self, transparent: bool) -> None:
        from qtextra.helpers import polish_widget

        self.transparent = transparent
        polish_widget(self)

    def mousePressEvent(self, evt: QEvent) -> None:
        if evt.button() == Qt.MouseButton.RightButton:
            self.on_right_click()
        elif evt.button() == Qt.MouseButton.LeftButton:
            self.on_click()
        super().mousePressEvent(evt)

    def set_toggle_qta(self, name: str, checked_name: str, connect: bool = True, **kwargs: ty.Any) -> None:
        checked_kwargs = deepcopy(kwargs)

        name, kwargs_ = get_icon(name)
        kwargs.update(kwargs_)
        checked_name, checked_kwargs_ = get_icon(checked_name)
        checked_kwargs.update(checked_kwargs_)
        self._qta_data = (name, kwargs)
        self._checked_qta_data = (checked_name, checked_kwargs)
        color_ = kwargs.pop("color", None)
        color_ = checked_kwargs.pop("color", color_)
        color = color_ or self._icon_color or THEMES.get_hex_color("icon")
        icon = qtawesome.icon(
            checked_name if self.isChecked() else name,
            **self._checked_qta_data[1] if self.isChecked() else self._qta_data[1],
            color=color,
        )
        self.setIcon(icon)
        if connect:
            self.toggled.connect(self._on_toggle)

    def _on_toggle(self) -> None:
        assert self._qta_data and self._checked_qta_data, "No qta data set."
        name = self._checked_qta_data[0] if self.isChecked() else self._qta_data[0]
        self._set_qta_icon(name, **self._checked_qta_data[1] if self.isChecked() else self._qta_data[1])

    def on_click(self) -> None:
        self.evt_click.emit(self)

    def on_right_click(self) -> None:
        self.evt_right_click.emit(self)

    def connect_to_right_click(self, func: ty.Callable) -> None:
        self.evt_right_click.connect(func)
        self.has_right_click = True
        hp.set_properties(self, {"right_click": True})

    def paintEvent(self, *args: ty.Any) -> None:
        super().paintEvent(*args)
        if self.menu_enabled:
            self._paint_menu_corner()
        elif self.has_right_click:
            self._paint_right_click_corner()

    def _paint_corner(self, color: str) -> None:
        rect = self.rect()
        glyph_size = max(5, min(14, int(rect.width() * 0.25)))
        margin = max(1, rect.width() // 12)
        right = rect.width() - margin
        bottom = rect.height() - margin
        points = [
            QPointF(right, bottom - glyph_size),
            QPointF(right - glyph_size, bottom),
            QPointF(right, bottom),
        ]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor(THEMES.get_hex_color(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF(points))

    def _paint_menu_corner(self) -> None:
        self._paint_corner("info")

    def _paint_right_click_corner(self) -> None:
        self._paint_corner("success")

    _onToggle = _on_toggle
    setCount = set_count
    setBadge = set_badge
    clearBadge = clear_badge
    setTransparent = set_transparent
    setToggleQta = set_toggle_qta
    onClick = on_click
    onRightClick = on_right_click
    connectToRightClick = connect_to_right_click


class QtTogglePushButton(QtImagePushButton):
    evt_toggled = Signal(bool)

    ICON_ON: str = ""
    ICON_OFF: str = ""

    _state: bool = False

    def __init__(self, *args, state: bool = False, auto_connect: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        if auto_connect:
            self.auto_connect()
        self.state = state

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, value: bool) -> None:
        changed = value != self._state
        self._state = value
        self.set_qta(self.ICON_ON if value else self.ICON_OFF)
        if changed:
            self.evt_toggled.emit(value)

    def set_state(self, state: bool, trigger: bool = True) -> None:
        with hp.qt_signals_blocked(self, block_signals=not trigger):
            self.state = state

    def auto_connect(self) -> None:
        self.evt_click.connect(self.toggle_state)

    def toggle_state(self) -> None:
        self.state = not self.state

    setState = set_state
    autoConnect = auto_connect
    toggleState = toggle_state


class QtAnimationPlayButton(QtTogglePushButton):
    ICON_ON = "stop"
    ICON_OFF = "start"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def playing(self) -> bool:
        return self.state

    @playing.setter
    def playing(self, state: bool) -> None:
        self.state = state


class QtPauseButton(QtTogglePushButton):
    ICON_ON = "start"
    ICON_OFF = "pause"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def paused(self) -> bool:
        return self.state

    @paused.setter
    def paused(self, state: bool) -> None:
        self.state = state


class QtLockButton(QtTogglePushButton):
    ICON_ON = "lock_closed"
    ICON_OFF = "lock_open"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def locked(self) -> bool:
        return self.state

    @locked.setter
    def locked(self, state: bool) -> None:
        self.state = state


class QtThemeButton(QtTogglePushButton):
    ICON_ON = "dark_theme"
    ICON_OFF = "light_theme"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def dark(self) -> bool:
        return self.state

    @dark.setter
    def dark(self, state: bool) -> None:
        self.state = state


class QtAndOrButton(QtTogglePushButton):
    ICON_ON = "and"
    ICON_OFF = "or"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def dark(self) -> bool:
        return self.state

    @dark.setter
    def dark(self, state: bool) -> None:
        self.state = state


class QtExpandButton(QtTogglePushButton):
    ICON_ON = "chevron_up"
    ICON_OFF = "chevron_down"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def expanded(self) -> bool:
        return self.state

    @expanded.setter
    def expanded(self, state: bool) -> None:
        self.state = state


class QtSortButton(QtTogglePushButton):
    ICON_ON = "sort_ascending"
    ICON_OFF = "sort_descending"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)


class QtToggleButton(QtTogglePushButton):
    ICON_ON = "toggle_on"
    ICON_OFF = "toggle_off"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def toggled(self) -> bool:
        return self.state

    @toggled.setter
    def toggled(self, state: bool) -> None:
        self.state = state


class QtVerticalDirectionButton(QtTogglePushButton):
    ICON_ON = "long_arrow_up"
    ICON_OFF = "long_arrow_down"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def up(self) -> bool:
        return self.state

    @up.setter
    def up(self, state: bool) -> None:
        self.state = state

    @property
    def down(self) -> bool:
        return not self.up


class QtHorizontalDirectionButton(QtTogglePushButton):
    ICON_ON = "long_arrow_right"
    ICON_OFF = "long_arrow_left"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def right(self) -> bool:
        return self.state

    @right.setter
    def right(self, state: bool) -> None:
        self.state = state

    @property
    def left(self) -> bool:
        return not self.left


class QtVisibleButton(QtTogglePushButton):
    ICON_ON = "visible_on"
    ICON_OFF = "visible_off"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def visible(self) -> bool:
        return self.state

    @visible.setter
    def visible(self, state: bool) -> None:
        self.state = state

    @property
    def hidden(self) -> bool:
        return not self.visible


class QtHiddenButton(QtTogglePushButton):
    ICON_ON = "visible_off"
    ICON_OFF = "visible_on"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def hidden(self) -> bool:
        return self.state

    @hidden.setter
    def hidden(self, state: bool) -> None:
        self.state = state

    @property
    def visible(self) -> bool:
        return not self.state


class QtFilterButton(QtTogglePushButton):
    ICON_ON = "filter_on"
    ICON_OFF = "filter_off"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)


class QtPinButton(QtTogglePushButton):
    ICON_ON = "pin_on"
    ICON_OFF = "pin_off"

    def __init__(self, *args: ty.Any, color: bool = False, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)
        if color:
            self.ICON_ON = "pin_on_color"
            self.ICON_OFF = "pin_off_color"

    @property
    def pin(self) -> bool:
        return self.state

    @pin.setter
    def pin(self, state: bool) -> None:
        self.state = state


class QtFullscreenButton(QtTogglePushButton):
    ICON_ON = "fullscreen"
    ICON_OFF = "maximize"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def fullscreen(self) -> bool:
        return self.state

    @fullscreen.setter
    def fullscreen(self, state: bool) -> None:
        self.state = state


class QtMinimizeButton(QtTogglePushButton):
    ICON_ON = "minimize"
    ICON_OFF = "maximize"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)

    @property
    def minimized(self) -> bool:
        return self.state

    @minimized.setter
    def minimized(self, state: bool) -> None:
        self.state = state


class QtBoolButton(QtTogglePushButton):
    ICON_ON = "true"
    ICON_OFF = "false"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)


class QtImageButton(QtTogglePushButton):
    ICON_ON = "images"
    ICON_OFF = "image"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)


class QtMaskButton(QtTogglePushButton):
    ICON_ON = "masks"
    ICON_OFF = "mask"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)


class QtNDisplayButton(QtTogglePushButton):
    ICON_ON = "2d"
    ICON_OFF = "3d"

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)


class QtMultiStatePushButton(QtImagePushButton):
    DEFAULT_STATE: str = ""
    STATE_TO_ICON: ty.ClassVar[dict[str, str]]
    STATE_TO_OPTION: ty.ClassVar[dict[str, str]]

    evt_changed = Signal(str)

    _state: str = ""
    _menu: QWidget | None
    _auto_show_menu_on_hover: bool

    def __init__(self, *args: ty.Any, auto_show_menu_on_hover: bool = True, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)
        self._menu = None
        self._auto_show_menu_on_hover = auto_show_menu_on_hover
        self.setMouseTracking(True)
        default_state = self.get_default_state()
        if default_state:
            self.state = default_state

    def get_default_state(self) -> str:
        return self.DEFAULT_STATE

    def get_state_to_icon(self) -> dict[str, str]:
        return self.STATE_TO_ICON

    def get_state_to_option(self) -> dict[str, str]:
        return self.STATE_TO_OPTION

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, state: str) -> None:
        self._state = state
        self.set_qta(self.get_state_to_icon()[state])
        self.evt_changed.emit(state)

    def set_state(self, state: str) -> None:
        self.state = state

    def set_auto_show_menu_on_hover(self, enabled: bool) -> None:
        self._auto_show_menu_on_hover = enabled

    def set_and_show_menu(self) -> None:
        state_to_option = self.get_state_to_option()
        state_to_icon = self.get_state_to_icon()
        menu = hp.make_menu(self)
        for state, label in state_to_option.items():
            hp.make_menu_item(
                self,
                label,
                icon=state_to_icon[state],
                func=partial(self.set_state, state=state),
                menu=menu,
            )
        self._menu = menu
        hp.show_below_widget(menu, self, x_offset=20)

    def on_click(self) -> None:
        if not self._auto_show_menu_on_hover:
            QTimer.singleShot(0, self.set_and_show_menu)
        super().on_click()

    def enterEvent(self, event: QEnterEvent | QEvent) -> None:
        if self._auto_show_menu_on_hover:
            self.set_and_show_menu()
        if isinstance(event, QEnterEvent):
            super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self._auto_show_menu_on_hover and self._menu is not None:
            self._menu.close()
            self._menu = None
        super().leaveEvent(event)

    setAndShowMenu = set_and_show_menu
    setAutoShowMenuOnHover = set_auto_show_menu_on_hover
    setState = set_state


class QtPriorityButton(QtMultiStatePushButton):
    DEFAULT_STATE = "normal"
    STATE_TO_ICON: ty.ClassVar[dict[str, str]] = {
        "low": "priority_low",
        "normal": "priority_normal",
        "high": "priority_high",
    }
    STATE_TO_OPTION: ty.ClassVar[dict[str, str]] = {"low": "Low", "normal": "Normal", "high": "High"}

    @property
    def priority(self) -> str:
        return self.state

    @priority.setter
    def priority(self, state: str) -> None:
        self.state = state


class QtStateButton(QtMultiStatePushButton):
    DEFAULT_STATE = "info"
    STATE_TO_ICON: ty.ClassVar[dict[str, str]] = {
        "success": "success",
        "debug": "debug",
        "info": "info",
        "warning": "warning",
        "error": "error",
    }
    STATE_TO_OPTION: ty.ClassVar[dict[str, str]] = {
        "success": "Success",
        "debug": "Debug",
        "info": "Info",
        "warning": "Warning",
        "error": "Error",
    }


class QtEmotionButton(QtMultiStatePushButton):
    DEFAULT_STATE = "happy"
    STATE_TO_ICON: ty.ClassVar[dict[str, str]] = {
        "happy": "happy",
        "neutral": "neutral",
        "sad": "sad",
    }
    STATE_TO_OPTION: ty.ClassVar[dict[str, str]] = {
        "happy": "Happy!",
        "neutral": "Neutral",
        "sad": "Sad",
    }


class QtMultiThemeButton(QtMultiStatePushButton):
    ICON_ON = "dark_theme"
    ICON_OFF = "light_theme"

    def __init__(self, *args: ty.Any, auto_connect: bool = False, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)
        THEMES.evt_theme_added.connect(self._sync_state_from_theme)
        THEMES.evt_theme_changed.connect(self._sync_state_from_theme)
        self._sync_state_from_theme()
        if auto_connect:
            self.auto_connect()

    def get_default_state(self) -> str:
        return THEMES.theme

    def get_state_to_option(self) -> dict[str, str]:
        return {theme: theme.replace("_", " ").title() for theme in THEMES.available_themes()}

    def get_state_to_icon(self) -> dict[str, str]:
        return {
            theme: "dark_theme" if THEMES[theme].type == "dark" else "light_theme"
            for theme in THEMES.available_themes()
        }

    def _sync_state_from_theme(self) -> None:
        theme = THEMES.theme
        state_to_icon = self.get_state_to_icon()
        if theme not in state_to_icon:
            return
        with hp.qt_signals_blocked(self):
            self.state = theme

    def auto_connect(self) -> None:
        self.evt_changed.connect(THEMES.set_theme)


class QtToolbarPushButton(QtImagePushButton):
    START_OPACITY = 1.0
    END_OPACITY = 0.2
    PULSE_RATE = 1000
    N_LOOPS = 5

    indicator: str = ""
    _title: str = ""
    _text: str = ""
    _tooltip = None
    _suppress_hover_tooltip = False

    panel_widget: QWidget | None = None
    about_widget: QWidget | None = None

    def __init__(self, *args: ty.Any, **kwargs: ty.Any):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)

        self.opacity = QGraphicsOpacityEffect()
        self.opacity.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity)
        self.opacity_anim = QPropertyAnimation(self.opacity, b"opacity", self)
        self.opacity_anim.currentLoopChanged.connect(self._loop_update)
        self.opacity_anim.finished.connect(self.stop_pulse)

        self.tooltip_timer = hp.make_periodic_timer(self, self._show_tooltip, 700, start=False)
        self.tooltip_timer.setSingleShot(True)

        self.evt_click.connect(self.stop_pulse)
        self.evt_click.connect(self._suppress_tooltip_until_leave)

    def setToolTip(self, text: str) -> None:
        self._text = text

    def setRichToolTip(self, title: str, content: str) -> None:
        self._title = title
        self._text = content

    def _get_position(self) -> QPoint:
        rect = self.rect()
        pos = self.mapToGlobal(rect.topRight())
        pos -= QPoint(0, 22)
        return pos

    def _on_tooltip_closed(self) -> None:
        self._tooltip = None

    def _suppress_tooltip_until_leave(self) -> None:
        self._suppress_hover_tooltip = True
        self.tooltip_timer.stop()
        hp.close_widget(self._tooltip)
        self._tooltip = None

    def _show_tooltip(self) -> None:
        if not self._text or self._tooltip is not None or self._suppress_hover_tooltip:
            return
        try:
            self._tooltip = QtRichToolTip.show_tooltip(
                title=self._title,
                content=self._text,
                target=self,
                parent=hp.get_main_window(self),
            )
            self._tooltip.destroyed.connect(self._on_tooltip_closed)
        except AttributeError:
            QToolTip.showText(self._get_position(), self._text, self)

    def event(self, evt: QEvent) -> bool:
        if evt.type() == QEvent.Type.Enter:
            if not self._tooltip and not self._suppress_hover_tooltip:
                self.tooltip_timer.start()
            evt.ignore()
        elif evt.type() == QEvent.Type.Leave:
            self._suppress_hover_tooltip = False
            self.tooltip_timer.stop()
            hp.close_widget(self._tooltip)
            self._tooltip = None
        return super().event(evt)

    @Slot(int)
    def _loop_update(self, loop: int) -> None:
        start, end = (self.START_OPACITY, self.END_OPACITY) if loop % 2 == 0 else (self.END_OPACITY, self.START_OPACITY)
        self.opacity_anim.setStartValue(start)
        self.opacity_anim.setEndValue(end)

    @Slot(str)
    @Slot(str, str)
    def set_indicator(self, indicator_type: str, about: str | None = None) -> None:
        assert indicator_type in [
            "",
            "success",
            "warning",
            "active",
        ], f"Cannot use `{indicator_type}` type of indicator."
        if not self.isCheckable():
            indicator_type = ""
        self.indicator = indicator_type
        self.start_pulse() if self.indicator else self.stop_pulse()

    @property
    def indicator_color(self) -> QColor:
        return QColor(THEMES.get_hex_color(INDICATOR_TYPES[self.indicator]))

    @property
    def edge_color(self) -> QColor:
        return QColor(THEMES.get_hex_color(INDICATOR_TYPES[self.indicator]))

    def paintEvent(self, *args: ty.Any) -> None:
        QPushButton.paintEvent(self, *args)

        if self.indicator and not self.isChecked():
            width = int(self.rect().width() / 6)
            radius = int(self.rect().width() / 10)
            pos = QPoint(self.rect().width() - width, width)

            paint = QPainter(self)
            pen = paint.pen()
            pen.setColor(self.edge_color)
            brush = QBrush(self.indicator_color)
            paint.setBrush(brush)
            paint.setPen(pen)
            paint.drawEllipse(pos, radius, radius)

    def start_pulse(self) -> None:
        if self.indicator and not self.isChecked():
            self.opacity_anim.setEasingCurve(QEasingCurve.Type.Linear)
            self.opacity_anim.setDuration(self.PULSE_RATE)
            self.opacity_anim.setStartValue(self.START_OPACITY)
            self.opacity_anim.setEndValue(self.END_OPACITY)
            self.opacity_anim.setLoopCount(self.N_LOOPS)
            self.opacity_anim.start()

    def stop_pulse(self) -> None:
        self.opacity_anim.stop()
        self.opacity.setOpacity(1.0)

    setIndicator = set_indicator
    _getPosition = _get_position
    startPulse = start_pulse
    stopPulse = stop_pulse


class QtLabelledToolbarPushButton(QWidget):
    LABEL_SPACING = 0

    def __init__(self, *args: ty.Any, elide: bool = True, **kwargs: ty.Any):
        self._label_hidden = False
        self._label_text = ""
        self._elide = elide
        super().__init__(*args, **kwargs)

        self.image_btn = QtToolbarPushButton()
        self.label = QLabel()
        self.label.setObjectName("toolbar_label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.label.setWordWrap(False)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.LABEL_SPACING)
        layout.addWidget(self.image_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.evt_click = self.image_btn.evt_click
        self.set_qta = self.image_btn.set_qta
        self.setText = self.image_btn.setText
        self.setChecked = self.image_btn.setChecked
        self.set_indicator = self.image_btn.set_indicator
        self.set_indicator = self.image_btn.set_indicator
        self.stop_pulse = self.image_btn.stop_pulse
        self.start_pulse = self.image_btn.start_pulse
        self.setCheckable = self.image_btn.setCheckable
        self.isChecked = self.image_btn.isChecked
        self.click = self.image_btn.click
        self.set_qta_size = self.image_btn.set_qta_size
        self.set_qta_size_preset = self.image_btn.set_qta_size_preset

    @property
    def label_hidden(self) -> bool:
        return self._label_hidden

    @label_hidden.setter
    def label_hidden(self, value: bool) -> None:
        self._label_hidden = value
        self.label.setHidden(value)
        self.updateGeometry()

    def set_label(self, text: str) -> None:
        self._label_text = text
        self._update_label_geometry()
        self.updateGeometry()

    @property
    def elide(self) -> bool:
        return self._elide

    @elide.setter
    def elide(self, value: bool) -> None:
        self._elide = value
        self._update_label_geometry()
        self.updateGeometry()

    def set_default_size(
        self,
        xxsmall: bool = False,
        xsmall: bool = False,
        small: bool = False,
        normal: bool = False,
        average: bool = False,
        medium: bool = False,
        large: bool = False,
        xlarge: bool = False,
        xxlarge: bool = False,
    ) -> None:
        if not any((xxsmall, xsmall, small, normal, average, medium, large, xlarge, xxlarge)):
            self._update_label_geometry()
            self.updateGeometry()
            return
        warnings.warn(
            "`set_default_size` is deprecated, use `set_qta_size_preset` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.image_btn.set_default_size(
            xxsmall=xxsmall,
            xsmall=xsmall,
            small=small,
            normal=normal,
            average=average,
            medium=medium,
            large=large,
            xlarge=xlarge,
            xxlarge=xxlarge,
        )
        self._update_label_geometry()
        self.updateGeometry()

    def set_qta_size_preset(self, preset: QtaSizePreset) -> None:
        self.image_btn.set_qta_size_preset(preset)
        self._update_label_geometry()
        self.updateGeometry()

    def _update_label_geometry(self) -> None:
        text = self._label_text.strip()
        if not text:
            self.label.clear()
            self.label.setFixedSize(0, 0)
            return

        metrics = self.label.fontMetrics()
        lines = text.splitlines() or [text]
        icon_width = self.image_btn.sizeHint().width()

        if self._elide:
            width = icon_width
            display_text = "\n".join(metrics.elidedText(line, Qt.TextElideMode.ElideRight, width) for line in lines)
        else:
            width = max(icon_width, max(metrics.horizontalAdvance(line) for line in lines) + 2)
            display_text = "\n".join(lines)

        self.label.setText(display_text)
        self.label.setFixedWidth(width)
        self.label.ensurePolished()
        self.label.setFixedHeight(self.label.sizeHint().height())

    def sizeHint(self) -> QSize:
        icon_size = self.image_btn.sizeHint()
        if self._label_hidden or not self._label_text.strip():
            return QSize(icon_size.width(), icon_size.height())

        spacing = self.layout().spacing() if self.layout() is not None else 0
        width = max(icon_size.width(), self.label.width())
        height = icon_size.height() + spacing + self.label.height()
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    setDefaultSize = set_default_size
    setQtaSizePreset = set_qta_size_preset
    setLabel = set_label


if __name__ == "__main__":
    import sys

    val = True

    def _main() -> None:
        from qtextra.assets import QTA_MAPPING
        from qtextra.utils.dev import qframe

        def _disable_toolbar_labels():
            nonlocal toolbar_buttons

            for btn in toolbar_buttons:
                btn.label_hidden = not btn.label_hidden

        toolbar_buttons = []

        app, frame, va = qframe(False)
        frame.setMinimumSize(800, 800)

        ha = QHBoxLayout()
        ha.addWidget(hp.make_btn(frame, "Toggle toolbar label visibility", func=_disable_toolbar_labels))
        va.addLayout(ha)

        ha = QHBoxLayout()
        va.addLayout(ha)

        lay = QVBoxLayout()
        ha.addLayout(lay)

        btn2 = QtImagePushButton(parent=frame)
        btn2.setObjectName("info")
        lay.addWidget(btn2)

        lay.addWidget(QtAnimationPlayButton(parent=frame, auto_connect=True))
        lay.addWidget(QtPauseButton(parent=frame, auto_connect=True))
        lay.addWidget(QtImageButton(parent=frame, auto_connect=True))
        lay.addWidget(QtMaskButton(parent=frame, auto_connect=True))
        lay.addWidget(QtNDisplayButton(parent=frame, auto_connect=True))
        lay.addWidget(QtLockButton(parent=frame, auto_connect=True))
        lay.addWidget(QtHorizontalDirectionButton(parent=frame, auto_connect=True))
        lay.addWidget(QtVisibleButton(parent=frame, auto_connect=True))
        lay.addWidget(QtHiddenButton(parent=frame, auto_connect=True))
        lay.addWidget(QtFilterButton(parent=frame, auto_connect=True))
        lay.addWidget(QtVerticalDirectionButton(parent=frame, auto_connect=True))
        lay.addWidget(QtToggleButton(parent=frame, auto_connect=True))
        lay.addWidget(QtExpandButton(parent=frame, auto_connect=True))
        lay.addWidget(QtSortButton(parent=frame, auto_connect=True))
        lay.addWidget(QtPinButton(parent=frame, auto_connect=True))
        lay.addWidget(QtFullscreenButton(parent=frame, auto_connect=True))
        lay.addWidget(QtMinimizeButton(parent=frame, auto_connect=True))
        lay.addWidget(QtThemeButton(parent=frame, auto_connect=True))
        lay.addWidget(QtBoolButton(parent=frame, auto_connect=True))
        lay.addWidget(QtAndOrButton(parent=frame, auto_connect=True))

        lay.addWidget(QtPriorityButton(parent=frame, auto_connect=True))
        lay.addWidget(QtStateButton(parent=frame, auto_connect=True))
        lay.addWidget(QtEmotionButton(parent=frame, auto_connect=True))
        lay.addWidget(QtMultiThemeButton(parent=frame, auto_connect=True, auto_show_menu_on_hover=False))

        ha.addWidget(hp.make_v_line())

        lay = QVBoxLayout()

        def _print_right_click() -> None:
            print("Right click")

        for i, (name, qta_name) in enumerate(QTA_MAPPING.items()):
            btn = QtImagePushButton()
            btn.set_qta_size_preset("large")
            if i % 2 == 0:
                btn.connect_to_right_click(_print_right_click)
            if i % 3 == 0:
                btn.set_count(i)
            if i % 5 == 0:
                btn.menu_enabled = True
            btn.set_qta(qta_name, scale_factor=1)
            btn.setToolTip(f"{name} :: {qta_name}")
            btn.setCheckable(True)
            lay.addWidget(btn)
            if i % 10 == 0:
                ha.addLayout(lay)
                lay = QVBoxLayout()
        ha.addWidget(hp.make_v_line())

        # lay = QVBoxLayout()
        # for i, (name, qta_name) in enumerate(QTA_MAPPING.items()):
        #     btn = QtToolbarPushButton()
        #     btn.set_qta(qta_name)
        #     btn.set_qta_size_preset("large")
        #     btn.setToolTip(f"{name} :: {qta_name}")
        #     lay.addWidget(btn)
        #     if i % 10 == 0:
        #         ha.addLayout(lay)
        #         lay = QVBoxLayout()
        # ha.addWidget(hp.make_v_line())

        lay = QVBoxLayout()
        for i, (name, qta_name) in enumerate(QTA_MAPPING.items()):
            btn = QtLabelledToolbarPushButton()
            toolbar_buttons.append(btn)
            btn.set_qta(qta_name)
            btn.set_label(name)
            btn.setToolTip(f"{name} :: {qta_name}")
            lay.addWidget(btn)
            if i == 10:
                ha.addLayout(lay)
                break

        ha.addWidget(hp.make_v_line())

        lay = QVBoxLayout()
        for i, (name, qta_name) in enumerate(QTA_MAPPING.items()):
            btn = QtImagePushButton()
            btn.set_qta(qta_name)
            btn.setText(name)
            btn.setToolTip(f"{name} :: {qta_name}")
            lay.addWidget(btn)
            if i == 10:
                ha.addLayout(lay)
                break

        frame.show()
        sys.exit(app.exec_())

    _main()
