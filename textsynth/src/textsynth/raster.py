from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import freetype
import numpy as np
from PIL import Image

from .layout import Layout
from .shaping import ShapedGlyph

_LOAD_FLAGS = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING
_IDENTITY = freetype.Matrix(0x10000, 0, 0, 0x10000)


@dataclass
class _Placement:
    glyph: ShapedGlyph
    x: float
    y: float
    rotation: float


def rasterize(
    lines: Sequence[Sequence[ShapedGlyph]],
    layout: Layout,
    *,
    rtl: bool = True,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng if rng is not None else np.random.default_rng()
    ss = max(1, int(layout.supersample))
    placements = _place(lines, layout, rtl=rtl, rng=rng, scale=ss)

    tiles = []
    for p in placements:
        tile = _render_glyph(p, layout.size * ss)
        if tile is not None:
            tiles.append(tile)

    left, top, right, bottom = layout.padding_box()
    if not tiles:
        return np.zeros((max(1, top + bottom), max(1, left + right)), dtype=np.float32)

    x0 = min(t[1] for t in tiles)
    y0 = min(t[2] for t in tiles)
    x1 = max(t[1] + t[0].shape[1] for t in tiles)
    y1 = max(t[2] + t[0].shape[0] for t in tiles)

    canvas = np.zeros((y1 - y0, x1 - x0), dtype=np.float32)
    for bitmap, bx, by in tiles:
        h, w = bitmap.shape
        region = canvas[by - y0 : by - y0 + h, bx - x0 : bx - x0 + w]
        np.maximum(region, bitmap, out=region)

    if ss > 1:
        canvas = _downsample(canvas, ss)

    return np.pad(canvas, ((top, bottom), (left, right)))


def _place(
    lines: Sequence[Sequence[ShapedGlyph]],
    layout: Layout,
    *,
    rtl: bool,
    rng: np.random.Generator,
    scale: int,
) -> list[_Placement]:
    size = layout.size * scale
    tracking = layout.tracking * scale
    word_spacing = layout.word_spacing * scale
    line_height = size * layout.line_spacing

    widths = [_line_width(line, size, tracking, word_spacing) for line in lines]
    max_width = max(widths, default=0.0)
    align = layout.align
    if align == "auto":
        align = "right" if rtl else "left"

    placements: list[_Placement] = []
    for i, (line, width) in enumerate(zip(lines, widths)):
        if align == "right":
            x = max_width - width
        elif align == "center":
            x = (max_width - width) / 2.0
        else:
            x = 0.0
        baseline = i * line_height

        shared = (0.0, 0.0, 0.0)

        for glyph in line:
            px_per_unit = size / glyph.font.upem
            dx = rng.normal(0.0, layout.jitter_x * scale) if layout.jitter_x else 0.0
            dy = rng.normal(0.0, layout.jitter_y * scale) if layout.jitter_y else 0.0
            rotation = rng.normal(0.0, layout.jitter_rotation) if layout.jitter_rotation else 0.0
            if glyph.x_advance:
                shared = (dx, dy, rotation)
            else:
                dx, dy, rotation = shared

            gx = x + glyph.x_offset * px_per_unit + dx
            gy = baseline - glyph.y_offset * px_per_unit + dy
            placements.append(_Placement(glyph, gx, gy, rotation))

            if glyph.x_advance:
                x += glyph.x_advance * px_per_unit + tracking
            if word_spacing and _is_space(glyph):
                x += word_spacing
    return placements


def _line_width(line: Sequence[ShapedGlyph], size: float, tracking: float, word_spacing: float) -> float:
    width = 0.0
    for glyph in line:
        if glyph.x_advance:
            width += glyph.x_advance * size / glyph.font.upem + tracking
        if word_spacing and _is_space(glyph):
            width += word_spacing
    return width


def _is_space(glyph: ShapedGlyph) -> bool:
    return glyph.gid == glyph.font.space_gid


def _render_glyph(p: _Placement, size: float) -> tuple[np.ndarray, int, int] | None:
    face = p.glyph.font.ft_face
    face.set_char_size(0, int(round(size * 64)), 72, 72)

    ix, iy = math.floor(p.x), math.floor(p.y)
    delta = freetype.Vector(int(round((p.x - ix) * 64)), -int(round((p.y - iy) * 64)))
    sx = p.glyph.x_scale
    if p.rotation or sx != 1.0:
        theta = math.radians(p.rotation)
        cos, sin = math.cos(theta), math.sin(theta)
        matrix = freetype.Matrix(
            int(cos * sx * 0x10000),
            int(-sin * 0x10000),
            int(sin * sx * 0x10000),
            int(cos * 0x10000),
        )
    else:
        matrix = _IDENTITY
    face.set_transform(matrix, delta)

    face.load_glyph(p.glyph.gid, _LOAD_FLAGS)
    bitmap = face.glyph.bitmap
    if bitmap.width == 0 or bitmap.rows == 0:
        return None

    pitch = abs(bitmap.pitch)
    data = np.array(bitmap.buffer, dtype=np.uint8).reshape(bitmap.rows, pitch)[:, : bitmap.width]
    if bitmap.pitch < 0:
        data = data[::-1]
    return data.astype(np.float32) / 255.0, ix + face.glyph.bitmap_left, iy - face.glyph.bitmap_top


def _downsample(ink: np.ndarray, factor: int) -> np.ndarray:
    h, w = ink.shape
    ph, pw = (-h) % factor, (-w) % factor
    if ph or pw:
        ink = np.pad(ink, ((0, ph), (0, pw)))
    h, w = ink.shape
    return ink.reshape(h // factor, factor, w // factor, factor).mean(axis=(1, 3))


def ink_to_image(
    ink: np.ndarray,
    *,
    foreground: tuple[int, int, int] | str = "black",
    background: tuple[int, int, int] | str = "white",
    mode: str = "L",
) -> Image.Image:
    fg = np.array(_as_rgb(foreground), dtype=np.float32)
    bg = np.array(_as_rgb(background), dtype=np.float32)
    alpha = np.clip(ink, 0.0, 1.0)[..., None]

    if mode == "RGBA":
        rgb = np.broadcast_to(fg, alpha.shape[:2] + (3,))
        out = np.concatenate([rgb, alpha * 255.0], axis=-1)
        return Image.fromarray(np.round(out).astype(np.uint8), mode="RGBA")

    rgb = bg + (fg - bg) * alpha
    if mode == "L":
        grey = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        return Image.fromarray(np.round(np.clip(grey, 0, 255)).astype(np.uint8), mode="L")
    return Image.fromarray(np.round(np.clip(rgb, 0, 255)).astype(np.uint8), mode="RGB")


def _as_rgb(color: tuple[int, int, int] | str) -> tuple[int, int, int]:
    if isinstance(color, str):
        from PIL import ImageColor

        return ImageColor.getrgb(color)[:3]
    return tuple(int(c) for c in color)


def image_to_ink(image: Image.Image, *, invert: bool | None = None) -> np.ndarray:
    grey = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
    if invert is None:
        invert = float(np.median(grey)) > 0.5
    return 1.0 - grey if invert else grey
