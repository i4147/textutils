from __future__ import annotations

import re
import typing as ty
import warnings
from functools import lru_cache, partial
from itertools import product
from pathlib import Path

import numpy as np
from koyo.json import read_json_data
from koyo.timer import MeasureTimer
from loguru import logger
from psygnal import EventedModel
from pydantic import ConfigDict, ValidationError, field_validator
from pydantic_extra_types.color import Color
from qtpy.QtCore import QDateTime, QTime, Signal
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QApplication, QWidget

from qtextra.assets import THEME_PATH
from qtextra.config.config import ConfigBase, _get_previous_configs
from qtextra.utils.appdirs import USER_CACHE_DIR


def time_to_qt_time(value: str) -> QTime:
    time = QTime()
    try:
        _, _ = value.split(":")
    except ValueError:
        return time
    return time.fromString(value, "HH:mm")


def parse_time(value: str) -> tuple[int, ...]:
    try:
        hh, mm = value.split(":")
        return int(hh), int(mm)
    except ValueError:
        return -1, -1


def get_builtin_theme_data(name: str) -> dict[str, ty.Any]:
    path = THEME_PATH / f"{name}.json"
    theme_data = read_json_data(path)
    if not isinstance(theme_data, dict):
        raise TypeError(f"Theme file must contain a JSON object: {path}")
    return theme_data


DARK_THEME = get_builtin_theme_data("dark")
LIGHT_THEME = get_builtin_theme_data("light")


class Theme(EventedModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str
    type: str
    syntax_style: str
    canvas: Color
    console: Color
    background: Color
    foreground: Color
    primary: Color
    secondary: Color
    highlight: Color
    text: Color
    icon: Color
    warning: Color
    error: Color
    success: Color
    info: Color = Color("rgb(0, 122, 204)")
    current: Color
    progress: Color
    standout: Color
    font_size: str = "14pt"
    header_size: str = "18pt"

    def __getattr__(self, item: str) -> str | Color:
        return getattr(self, item)

    @field_validator(
        "canvas",
        "console",
        "background",
        "foreground",
        "primary",
        "secondary",
        "highlight",
        "text",
        "icon",
        "warning",
        "error",
        "success",
        "info",
        "current",
        "progress",
        "standout",
        mode="before",
    )
    def _validate_color(value) -> Color:
        if isinstance(value, np.ndarray):
            value = value.tolist()
        elif isinstance(value, str):
            value = Color(value).as_hex()
        return Color(value)

    @field_validator("syntax_style", mode="before")
    def _ensure_syntax_style(value: str) -> str:
        from pygments.styles import STYLE_MAP

        assert value in STYLE_MAP, (
            f"Incorrect `syntax_style` value provided. Please use one of the following: {', '.join(STYLE_MAP)}"
        )
        return value

    @field_validator("font_size", "header_size", mode="before")
    def _ensure_font_size(value: int | str) -> str:
        if isinstance(value, int):
            value = str(value)
        value = value.replace("px", "").replace("pt", "")
        if not value.endswith("pt"):
            return value + "pt"
        return value

    @property
    def id(self) -> str:
        return self.name

    def to_dict(self) -> dict:
        data = {}
        for key, value in self:
            if isinstance(value, Color):
                data[key] = value.as_hex()
            else:
                data[key] = value
        return data


class Themes(ConfigBase):
    DEFAULT_CONFIG_NAME = "themes-config.json"
    DEFAULT_CONFIG_GROUPS = ("settings",)
    EXTRA_CONFIG_GROUPS = ("themes",)

    REQUIRED_KEYS = (
        "name",
        "type",
        "background",
        "foreground",
        "primary",
        "secondary",
        "highlight",
        "text",
        "icon",
        "warning",
        "error",
        "success",
        "info",
        "progress",
        "current",
        "syntax_style",
        "console",
        "canvas",
        "standout",
    )

    evt_theme_added = Signal()
    evt_theme_changed = Signal()
    evt_update_timer = Signal()
    evt_theme_icon_changed = Signal()
    evt_qss_changed = Signal()

    def __init__(self):
        super().__init__(None)

        self._theme: str = "light"
        self._sync_with_time: bool = True
        self._light_start_time: str = "08:00"
        self._light_end_time: str = "20:00"
        self.themes: dict[str, Theme] = {}
        self._load_builtin_themes()
        try:
            from napari.utils.theme import _themes

            for name in _themes:
                _themes[name].icon = self.get_hex_color("icon")
        except ImportError:
            pass

    @staticmethod
    def _get_builtin_theme_paths() -> list[Path]:
        priority = {
            "light": 0,
            "dark": 1,
        }
        return sorted(THEME_PATH.glob("*.json"), key=lambda path: (priority.get(path.stem, 99), path.stem))

    def _load_builtin_themes(self) -> None:
        for path in self._get_builtin_theme_paths():
            theme_data = get_builtin_theme_data(path.stem)
            self.add_theme(theme_data["name"], Theme(**theme_data))

    def __getitem__(self, item):
        return self.themes[item]

    @property
    def active(self) -> Theme:
        return self.themes[self.theme]

    def get_sync_theme(self) -> str:
        curr_time: QTime = QDateTime.currentDateTime().time()
        start_time = time_to_qt_time(self.light_start_time)
        end_time = time_to_qt_time(self.light_end_time)
        if start_time <= curr_time <= end_time:
            return "light"
        return "dark"

    def synchronize_theme(self) -> None:
        if self.sync_with_time:
            theme = self.get_sync_theme()
            self.theme = theme

    @property
    def sync_with_time(self) -> bool:
        return self._sync_with_time

    @sync_with_time.setter
    def sync_with_time(self, value: bool):
        self._sync_with_time = value
        self.evt_update_timer.emit()

    @property
    def light_start_time(self) -> str:
        return self._light_start_time

    @light_start_time.setter
    def light_start_time(self, value: str) -> None:
        self._light_start_time = value
        self.synchronize_theme()

    @property
    def light_end_time(self) -> str:
        return self._light_end_time

    @light_end_time.setter
    def light_end_time(self, value: str) -> None:
        self._light_end_time = value
        self.synchronize_theme()

    def set_theme(self, value: str) -> None:
        self.theme = value

    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, value: str) -> None:
        if self._theme == value:
            return
        if value not in self.themes:
            raise ValueError(f"Unrecognized theme {value}. Available themes are {self.available_themes()}")
        self._theme = value
        try:
            from napari.utils.theme import _themes

            for name in _themes:
                _themes[name].icon = self.get_hex_color("icon")
        except ImportError:
            pass
        with MeasureTimer() as timer:
            self.evt_theme_changed.emit()
            self.evt_theme_icon_changed.emit()
        logger.debug(f"Changed theme to '{value}' in {timer()}")

    @staticmethod
    def update_palette() -> None:
        qapp = QApplication.instance()
        if qapp is None:
            return
        palette = qapp.palette()
        palette.setColor(QPalette.ColorRole.Link, QColor("#f56833"))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#f56833"))
        qapp.setPalette(palette)

    @property
    def syntax_style(self) -> str:
        return self.active.syntax_style

    def get_font_size(self) -> int:
        unit = "pt" if "pt" in self.active.font_size else "px"
        return int(self.active.font_size.split(unit)[0])

    def get_rgb_color(self, name: str) -> str:
        color: Color = getattr(self.active, name)
        return color.as_rgb()

    def get_hex_color(self, name: str) -> str:
        try:
            color: Color = getattr(self.active, name)
            return color.as_hex(format="long")
        except RecursionError:
            warnings.warn(
                f"Failed to get hex color for {name}. This may be caused by a recursive reference in the theme"
                f" configuration.",
                stacklevel=2,
            )
            return "#000000"

    def get_qt_color(self, name: str) -> QColor:
        color = self.get_hex_color(name)
        return QColor(color)

    @staticmethod
    def get_text_color_for_background(color: str) -> str:
        from qtextra.utils.color import get_text_color, rgb_to_hex

        color = QColor(color)
        return rgb_to_hex(get_text_color(color).getRgb())

    def get_theme(
        self,
        theme_name: str | None = None,
        as_dict: bool = False,
    ) -> Theme | dict[str, str]:
        if theme_name is None:
            theme_name = self.theme
        if theme_name in self.themes:
            theme = self.themes[theme_name]
            _theme = theme.model_copy()
            if as_dict:
                return _theme.to_dict()
            return _theme
        raise ValueError(f"Unrecognized theme {theme_name}. Available themes are {self.available_themes()}")

    @property
    def is_dark(self) -> bool:
        return self.active.type == "dark"

    def add_theme(self, name: str, theme_data: Theme | dict[str, str], register: bool = False):
        is_new_theme = name not in self.themes
        if name not in self.themes:
            self.add_resource(name)
        if isinstance(theme_data, dict):
            theme_data = Theme(**theme_data)

        self.themes[name] = theme_data
        self.themes[name].events.icon.connect(partial(self._emit_icon_color_change, name), max_args=0)
        self.themes[name].events.connect(self._emit_theme_changed, max_args=0)
        if register:
            self.register_themes([name])
        if is_new_theme:
            self.evt_theme_added.emit()

    def add_resource(self, name: str) -> None:
        from qtpy.QtCore import QDir

        QDir.addSearchPath(f"theme_{name}", str(self.get_theme_path(name)))
        logger.trace(f"Added '{name}' theme to resources path")

    def register_themes(self, names: list[str] | None = None) -> None:
        from qtextra.icons import build_theme_svgs

        if names is None:
            names = list(self.themes.keys())

        for name in names:
            build_theme_svgs(name)

    def available_themes(self) -> tuple[str, ...]:
        return tuple(self.themes)

    def get_theme_color(self, key: str = "text", theme_name: str | None = None) -> str:
        if theme_name is None:
            theme_name = self.theme
        palette = self.themes[theme_name]
        return getattr(palette, key).as_hex()

    def get_theme_stylesheet(self, theme_name: str | None = None) -> str:
        from qtextra.assets import get_stylesheet
        from qtextra.utils.template import template

        if theme_name is None:
            theme_name = self.theme
        palette = self.themes[theme_name].to_dict()
        palette["theme_path"] = self.get_theme_path(theme_name).as_posix()
        stylesheet = get_stylesheet()
        stylesheet = template(stylesheet, **palette)
        return self._resolve_theme_icon_urls(stylesheet, theme_name)

    get_stylesheet = get_theme_stylesheet

    def set_theme_stylesheet(self, widget: QWidget, theme_name: str | None = None) -> None:
        widget.setStyleSheet(self.get_theme_stylesheet(theme_name))

    set_stylesheet = set_theme_stylesheet

    def apply(self, widget: QWidget) -> None:
        self.set_theme_stylesheet(widget)

    @staticmethod
    def _resolve_theme_icon_urls(stylesheet: str, theme_name: str) -> str:
        theme_path = Themes.get_theme_path(theme_name).as_posix().rstrip("/")
        prefix = f"theme_{theme_name}:"
        stylesheet = stylesheet.replace(f"{prefix}//", f"{theme_path}/")
        stylesheet = stylesheet.replace(f"{prefix}/", f"{theme_path}/")
        return stylesheet.replace(prefix, f"{theme_path}/")

    @staticmethod
    def get_theme_path(theme_name: str) -> Path:
        from qtextra.utils.appdirs import USER_THEME_DIR

        return USER_THEME_DIR / theme_name

    def _get_config_parameters(self, config: dict) -> dict:
        config["themes"] = {}
        for name, theme in self.themes.items():
            config["themes"][name] = theme.to_dict()
        config["settings"] = {
            "theme": self.theme,
            "sync_with_time": self._sync_with_time,
            "light_start_time": self._light_start_time,
            "light_end_time": self._light_end_time,
        }
        return config

    def _emit_icon_color_change(self, name: str) -> None:
        self.register_themes([name])
        self.evt_theme_icon_changed.emit()
        logger.debug(f"Updating icon color for '{name}'...")

    def _emit_theme_changed(self) -> None:
        self.evt_theme_changed.emit()

    def _set_config_parameters(self, config: dict) -> None:
        for config_group_title in ("themes",):
            _config_group = config.get(config_group_title, {})
            for theme_name, theme in _config_group.items():
                try:
                    if theme_name in self.themes:
                        for key, value in theme.items():
                            try:
                                setattr(self.themes[theme_name], key, value)
                            except ValidationError as err:
                                logger.warning(
                                    f"Failed setting of {key} because it did not pass validation."
                                    f"\nFailed with error=`{err}`",
                                )
                    else:
                        self.add_theme(theme_name, theme)
                except ValidationError as err:
                    logger.warning(
                        f"Skipping {theme_name} theme because it did not pass validation.\nFailed with error=`{err}`",
                    )
                except (AttributeError, TypeError, ValueError) as err:
                    logger.warning(f"Could not load theme data for '{theme_name}': {err}")

    def lighten(self, color: str, percentage: float = 10, as_hex: bool = False) -> str:
        from qtextra.utils.template import lighten

        color = lighten(color, percentage)
        if as_hex:
            color = Color(color).as_hex()
        return color

    def darken(self, color: str, percentage: float = 10, as_hex: bool = False) -> str:
        from qtextra.utils.template import darken

        color = darken(color, percentage)
        if as_hex:
            color = Color(color).as_hex()
        return color


def get_previous_configs(base_dir: str | None = None, filename: str = "themes-config.json") -> dict[str, str]:
    return _get_previous_configs(base_dir, filename)


svg_elem = re.compile(r"(<svg[^>]*>)")
svg_style = """<style type="text/css">
path {{fill: {0}; opacity: {1};}}
polygon {{fill: {0}; opacity: {1};}}
circle {{fill: {0}; opacity: {1};}}
rect {{fill: {0}; opacity: {1};}}
</style>"""


def get_theme_cache_dir(theme_name: str) -> Path:
    return Path(USER_CACHE_DIR) / "_themes" / theme_name


@lru_cache
def get_raw_svg(path: str) -> str:
    return Path(path).read_text()


@lru_cache
def get_colorized_svg(path_or_xml: str | Path, color: str | None = None, opacity=1) -> str:
    path_or_xml = str(path_or_xml)
    xml = path_or_xml if "</svg>" in path_or_xml else get_raw_svg(path_or_xml)
    if not color:
        return xml

    if not svg_elem.search(xml):
        raise ValueError(f"Could not detect svg tag in {path_or_xml!r}")
    return svg_elem.sub(f"\\1{svg_style.format(color, opacity)}", xml)


def generate_colorized_svgs(
    svg_paths: ty.Iterable[str | Path],
    colors: ty.Iterable[str | tuple[str, str]],
    opacities: ty.Iterable[float] = (1.0,),
    theme_override: dict[str, str] | None = None,
) -> ty.Iterator[tuple[str, str]]:
    theme_override = theme_override or {}

    ALIAS_T = "{color}/{svg_stem}{opacity}.svg"

    for color, path, op in product(colors, svg_paths, opacities):
        clrkey = color
        svg_stem = Path(path).stem
        if isinstance(color, tuple):
            clrkey, theme_key = color
            theme_key = theme_override.get(svg_stem, theme_key)
            color = getattr(THEMES.get_theme(clrkey, False), theme_key).as_hex()

        op_key = "" if op == 1 else f"_{op * 100:.0f}"
        alias = ALIAS_T.format(color=clrkey, svg_stem=svg_stem, opacity=op_key)
        yield alias, get_colorized_svg(path, color, op)


def write_colorized_svgs(
    dest: str | Path,
    svg_paths: ty.Iterable[str | Path],
    colors: ty.Iterable[str | tuple[str, str]],
    opacities: ty.Iterable[float] = (1.0,),
    theme_override: dict[str, str] | None = None,
):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    svgs = generate_colorized_svgs(
        svg_paths=svg_paths,
        colors=colors,
        opacities=opacities,
        theme_override=theme_override,
    )

    for alias, svg in svgs:
        (dest / Path(alias).name).write_text(svg)


def build_theme_svgs(theme_name: str) -> str:
    from qtextra.assets import ICONS

    out = get_theme_cache_dir(theme_name)
    write_colorized_svgs(
        out,
        svg_paths=ICONS.values(),
        colors=[(theme_name, "icon")],
        opacities=(0.5, 1),
        theme_override={"warning": "warning", "logo_silhouette": "background"},
    )
    return str(out)


def is_dark() -> bool:
    return THEMES.is_dark


class QtStyler:
    @classmethod
    def background(cls) -> QColor:
        return THEMES.get_qt_color("background")

    @classmethod
    def background_muted(cls) -> QColor:
        color = THEMES.get_qt_color("background")
        return color.lighter(10) if is_dark() else color.darker(20)

    @classmethod
    def foreground(cls) -> QColor:
        return THEMES.get_qt_color("foreground")

    @classmethod
    def primary(cls) -> QColor:
        return THEMES.get_qt_color("primary")

    @classmethod
    def secondary(cls) -> QColor:
        return THEMES.get_qt_color("secondary")

    @classmethod
    def highlight(cls) -> QColor:
        return THEMES.get_qt_color("highlight")

    @classmethod
    def highlight_muted(cls) -> QColor:
        color = THEMES.get_qt_color("highlight")
        return color.darker(20) if is_dark() else color.lighter(50)

    @classmethod
    def text(cls) -> QColor:
        return THEMES.get_qt_color("text")

    @classmethod
    def text_muted(cls) -> QColor:
        color = THEMES.get_qt_color("text")
        return color.lighter(50) if is_dark() else color.darker(50)

    @classmethod
    def icon(cls) -> QColor:
        return THEMES.get_qt_color("icon")

    @classmethod
    def warning(cls) -> QColor:
        return THEMES.get_qt_color("warning")

    @classmethod
    def error(cls) -> QColor:
        return THEMES.get_qt_color("error")

    @classmethod
    def success(cls) -> QColor:
        return THEMES.get_qt_color("success")

    @classmethod
    def progress(cls) -> QColor:
        return THEMES.get_qt_color("progress")

    @classmethod
    def current(cls) -> QColor:
        return THEMES.get_qt_color("current")


THEMES: Themes = Themes()
THEMES.register_themes()
