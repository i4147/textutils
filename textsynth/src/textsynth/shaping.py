from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import uharfbuzz as hb

from .fonts import Font, FontLike

DEFAULT_FEATURES: dict[str, bool] = {"kern": True, "liga": True, "rlig": True, "calt": True}


@dataclass(frozen=True)
class ShapedGlyph:
    gid: int
    cluster: int
    x_advance: float
    y_advance: float
    x_offset: float
    y_offset: float
    font: Font
    x_scale: float = 1.0
    """The horizontal stretch to apply at draw time, about the glyph origin.

    HarfBuzz never sets this value. It is for a glyph rule that must use
    one outline at many lengths. A swept tail is the primary example. The
    rule can then use one glyph instead of a new glyph for each length.
    The advance does not change. Thus a stretched glyph goes across its
    neighbours, but it does not move them.
    """

    @property
    def name(self) -> str:
        return self.font.glyph_name(self.gid)


@dataclass
class ShapeOptions:
    direction: str | None = None
    """Either ``"rtl"`` or ``"ltr"``. ``None`` gets the direction from the script."""
    script: str | None = None
    language: str | None = None
    features: dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_FEATURES))

    def merged_features(self, extra: dict[str, bool] | None = None) -> dict[str, bool]:
        merged = dict(self.features)
        if extra:
            merged.update(extra)
        return merged


def shape(
    text: str,
    font: FontLike,
    options: ShapeOptions | None = None,
    *,
    fallbacks: Sequence[FontLike] = (),
) -> list[ShapedGlyph]:
    options = options or ShapeOptions()
    primary = Font.load(font)
    fallback_fonts = [Font.load(f) for f in fallbacks]

    runs = _split_runs(text, primary, fallback_fonts)
    shaped = [(_shape_run(run_text, run_font, options), start) for run_text, run_font, start in runs]

    if is_rtl(text, options):
        shaped.reverse()

    glyphs: list[ShapedGlyph] = []
    for run_glyphs, start in shaped:
        for g in run_glyphs:
            glyphs.append(
                ShapedGlyph(g.gid, g.cluster + start, g.x_advance, g.y_advance, g.x_offset, g.y_offset, g.font)
            )
    return glyphs


def is_rtl(text: str, options: ShapeOptions | None = None) -> bool:
    if options and options.direction:
        return options.direction.lower() == "rtl"
    buf = hb.Buffer()
    buf.add_str(text or " ")
    buf.guess_segment_properties()
    return str(buf.direction).lower() == "rtl"


def _shape_run(text: str, font: Font, options: ShapeOptions) -> list[ShapedGlyph]:
    if not text:
        return []
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if options.direction:
        buf.direction = options.direction
    if options.script:
        buf.script = options.script
    if options.language:
        buf.language = options.language

    hb.shape(font.hb_font, buf, options.merged_features())

    return [
        ShapedGlyph(
            gid=info.codepoint,
            cluster=info.cluster,
            x_advance=pos.x_advance,
            y_advance=pos.y_advance,
            x_offset=pos.x_offset,
            y_offset=pos.y_offset,
            font=font,
        )
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions)
    ]


def _split_runs(text: str, primary: Font, fallbacks: Sequence[Font]) -> list[tuple[str, Font, int]]:
    if not text:
        return []
    if not fallbacks:
        return [(text, primary, 0)]

    runs: list[tuple[str, Font, int]] = []
    current_font: Font | None = None
    start = 0
    for i, ch in enumerate(text):
        font = current_font if (ch.isspace() and current_font) else _font_for(ch, primary, fallbacks)
        if current_font is None:
            current_font, start = font, i
        elif font is not current_font:
            runs.append((text[start:i], current_font, start))
            current_font, start = font, i
    runs.append((text[start:], current_font or primary, start))
    return runs


def _font_for(ch: str, primary: Font, fallbacks: Iterable[Font]) -> Font:
    if primary.covers(ch):
        return primary
    for font in fallbacks:
        if font.covers(ch):
            return font
    return primary
