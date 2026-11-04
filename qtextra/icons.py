from __future__ import annotations

import re
import typing as ty
from functools import lru_cache
from itertools import product
from pathlib import Path


def get_icon_path(name: str) -> str:
    from qtextra.assets import ICONS

    if name not in ICONS:
        raise ValueError(f"unrecognized icon name: {name!r}. Known names: {ICONS}")
    return ICONS[name]


svg_elem = re.compile(r"(<svg[^>]*>)")
svg_style = """<style type="text/css">
path {{fill: {0}; opacity: {1};}}
polygon {{fill: {0}; opacity: {1};}}
circle {{fill: {0}; opacity: {1};}}
rect {{fill: {0}; opacity: {1};}}
</style>"""


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
    from qtextra.config.theme import THEMES

    theme_override = theme_override or {}

    ALIAS_T = "{color}/{svg_stem}{opacity}.svg"

    for color, path, op in product(colors, svg_paths, opacities):
        clrkey = color
        svg_stem = Path(path).stem
        if isinstance(color, tuple):
            clrkey, theme_key = color
            theme_key = theme_override.get(svg_stem, theme_key)
            color = getattr(THEMES[clrkey], theme_key).as_hex()

        op_key = "" if op == 1 else f"_{op * 100:.0f}"
        alias = ALIAS_T.format(color=clrkey, svg_stem=svg_stem, opacity=op_key)
        yield alias, get_colorized_svg(path, color, op)


def write_colorized_svgs(
    dest: str | Path,
    svg_paths: ty.Iterable[str | Path],
    colors: ty.Iterable[str | tuple[str, str]],
    opacities: ty.Iterable[float] = (1.0,),
    theme_override: dict[str, str] | None = None,
) -> None:
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
    from qtextra.config.theme import THEMES

    out = THEMES.get_theme_path(theme_name)
    write_colorized_svgs(
        out,
        svg_paths=ICONS.values(),
        colors=[(theme_name, "icon")],
        opacities=(0.5, 1),
        theme_override={
            "warning": "warning",
            "error": "error",
            "logo_silhouette": "background",
        },
    )
    with (out / "plugin.txt").open("w") as f:
        f.write("builtin")
    return str(out)
