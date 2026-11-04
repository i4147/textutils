from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence, runtime_checkable

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import SVGPath

from .fonts import Font, FontLike


@dataclass
class Outline:
    draw: Callable[[Any], None]
    advance: float

    def bounds(self) -> tuple[float, float, float, float] | None:
        pen = BoundsPen(None)
        self.draw(pen)
        return pen.bounds


@runtime_checkable
class GlyphSource(Protocol):
    def build(self, target_upem: int) -> Outline: ...


@dataclass
class SVGGlyph:
    source: str | Path | bytes
    height: float = 1.0
    """The height of the SVG viewBox, in ems."""
    descend: float = 0.2
    """The distance from the baseline down to the bottom of the viewBox, in ems."""
    left_bearing: float = 0.0
    """The left side bearing, in ems."""
    right_bearing: float = 0.0
    """The right side bearing, in ems."""
    advance: float | None = None
    """The advance width in ems.

    The default is the scaled viewBox width plus the two side bearings.
    """
    reverse_contours: bool = False
    """Invert the contour direction. Set this if the counters fill with ink."""

    def build(self, target_upem: int) -> Outline:
        markup = _read_svg(self.source)
        vb_x, vb_y, vb_w, vb_h = _viewbox(markup)

        scale = (self.height * target_upem) / vb_h
        lsb = self.left_bearing * target_upem
        transform = (
            scale,
            0.0,
            0.0,
            -scale,
            -vb_x * scale + lsb,
            (vb_y + vb_h) * scale - self.descend * target_upem,
        )
        advance = (
            self.advance * target_upem
            if self.advance is not None
            else vb_w * scale + lsb + self.right_bearing * target_upem
        )

        def draw(pen: Any) -> None:
            target = ReverseContourPen(pen) if self.reverse_contours else pen
            SVGPath.fromstring(markup, transform=transform).draw(target)

        return Outline(draw, advance)


@dataclass
class BorrowedGlyph:
    font: FontLike
    glyph: str
    """One character to find in the cmap of the donor font, or a glyph name."""
    scale: float = 1.0
    dx: float = 0.0
    """The horizontal offset, in ems."""
    dy: float = 0.0
    """The vertical offset, in ems."""
    advance: float | None = None
    """The advance width in ems. The default is the scaled donor advance."""

    def build(self, target_upem: int) -> Outline:
        donor = Font.load(self.font)
        tt = donor.ttfont()
        name = self._resolve(donor, tt)
        glyph_set = tt.getGlyphSet()
        scale = self.scale * target_upem / donor.upem
        transform = (scale, 0.0, 0.0, scale, self.dx * target_upem, self.dy * target_upem)

        recording = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(recording)

        def draw(pen: Any) -> None:
            recording.replay(TransformPen(pen, transform))

        advance = self.advance * target_upem if self.advance is not None else tt["hmtx"][name][0] * scale
        return Outline(draw, advance)

    def _resolve(self, donor: Font, tt: Any) -> str:
        if len(self.glyph) == 1:
            name = tt.getBestCmap().get(ord(self.glyph))
            if name:
                return name
        if self.glyph in tt.getGlyphOrder():
            return self.glyph
        raise KeyError(f"{donor.name} has no glyph {self.glyph!r}")


@dataclass
class CompositeGlyph:
    parts: Sequence[GlyphSource]
    overlap: float = 0.0
    """The width to take out between each pair of neighbours, in ems.

    Raise it to tuck the parts into each other. The advance narrows by
    the same amount, thus the letters around the glyph follow it in.
    """
    advance: float | None = None
    """The advance width in ems. The default is the sum of the parts,
    less the overlaps."""

    def build(self, target_upem: int) -> Outline:
        if not self.parts:
            raise ValueError("CompositeGlyph needs at least one part")
        built = [part.build(target_upem) for part in self.parts]
        gap = self.overlap * target_upem

        offsets: list[float] = []
        x = 0.0
        for outline in built:
            offsets.append(x)
            x += outline.advance - gap
        total = x + gap

        if self.advance is None and total <= 0:
            raise ValueError(
                f"overlap {self.overlap} leaves the glyph an advance of {total / target_upem:.3f} "
                "ems; lower the overlap or set advance"
            )

        def draw(pen: Any) -> None:
            for outline, dx in zip(built, offsets):
                outline.draw(TransformPen(pen, (1.0, 0.0, 0.0, 1.0, dx, 0.0)))

        return Outline(draw, self.advance * target_upem if self.advance is not None else total)


@dataclass
class PenGlyph:
    draw_with: Callable[[Any, int], None]
    advance: float = 1.0
    """The advance width, in ems."""

    def build(self, target_upem: int) -> Outline:
        return Outline(lambda pen: self.draw_with(pen, target_upem), self.advance * target_upem)


def _read_svg(source: str | Path | bytes) -> str:
    if isinstance(source, bytes):
        return source.decode("utf-8")
    text = str(source)
    if "<" in text and ">" in text:
        return text
    return Path(source).read_text(encoding="utf-8")


def _viewbox(markup: str) -> tuple[float, float, float, float]:
    match = re.search(r'viewBox\s*=\s*"([^"]+)"', markup)
    if match:
        parts = [float(v) for v in re.split(r"[,\s]+", match.group(1).strip()) if v]
        if len(parts) == 4:
            return parts[0], parts[1], parts[2], parts[3]
    width = _length(markup, "width")
    height = _length(markup, "height")
    if width and height:
        return 0.0, 0.0, width, height
    raise ValueError("SVG has neither a viewBox nor width/height; cannot scale it")


def _length(markup: str, attr: str) -> float | None:
    match = re.search(rf'\b{attr}\s*=\s*"([0-9.]+)', markup)
    return float(match.group(1)) if match else None
