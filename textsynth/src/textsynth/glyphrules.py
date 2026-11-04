from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence

import numpy as np

from .fonts import Font
from .layout import Layout
from .patching import FontPatch
from .shaping import ShapedGlyph, ShapeOptions, shape


@dataclass
class LineContext:
    text: str
    """The line, after the text rules have run."""
    font: Font
    """The patched font that shaped the line."""
    layout: Layout
    options: ShapeOptions = field(default_factory=ShapeOptions)
    rtl: bool = True
    fallbacks: Sequence[Font] = ()

    def shape(self, text: str | None = None, font: Font | None = None) -> list[ShapedGlyph]:
        return shape(
            self.text if text is None else text,
            self.font if font is None else font,
            self.options,
            fallbacks=self.fallbacks,
        )

    def units(self, pixels: float, font: Font | None = None) -> float:
        target = font or self.font
        size = self.layout.size or 1.0
        return pixels * target.upem / size


class GlyphRule(Protocol):
    def patches(self) -> Sequence[FontPatch]: ...

    def apply(self, glyphs: Sequence[ShapedGlyph], ctx: LineContext, rng: np.random.Generator) -> list[ShapedGlyph]: ...


def rule_patches(rules: Sequence[GlyphRule]) -> list[FontPatch]:
    patches: list[FontPatch] = []
    for rule in rules:
        patches.extend(rule.patches())
    return patches
