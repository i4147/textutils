from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from PIL import Image

from .effects import Effect
from .fonts import Font, FontLike
from .glyphrules import GlyphRule, LineContext, rule_patches
from .layout import Layout
from .patching import FontPatch, patch_font
from .raster import ink_to_image, rasterize
from .shaping import ShapedGlyph, ShapeOptions, is_rtl, shape
from .textrules import TextRule


@dataclass
class Synthesizer:
    font: FontLike
    layout: Layout = field(default_factory=Layout)
    text_rules: Sequence[TextRule] = ()
    font_patches: Sequence[FontPatch] = ()
    glyph_rules: Sequence[GlyphRule] = ()
    effects: Sequence[Effect] = ()
    fallbacks: Sequence[FontLike] = ()
    shape_options: ShapeOptions = field(default_factory=ShapeOptions)
    foreground: tuple[int, int, int] | str = "black"
    background: tuple[int, int, int] | str = "white"
    mode: str = "L"
    seed: int | None = None

    def __post_init__(self) -> None:
        self._base_font = Font.load(self.font)
        self._patched: Font | None = None
        self._fallback_fonts = [Font.load(f) for f in self.fallbacks]

    @property
    def patched_font(self) -> Font:
        if self._patched is None:
            patches = [*self.font_patches, *rule_patches(self.glyph_rules)]
            self._patched = patch_font(self._base_font, patches)
        return self._patched

    def invalidate(self) -> None:
        self._patched = None

    def __call__(self, text: str, *, seed: int | None = None) -> Image.Image:
        return self.render(text, seed=seed)

    def render(self, text: str, *, seed: int | None = None) -> Image.Image:
        ink = self.render_ink(text, seed=seed)
        return ink_to_image(ink, foreground=self.foreground, background=self.background, mode=self.mode)

    def render_ink(self, text: str, *, seed: int | None = None) -> np.ndarray:
        rng = np.random.default_rng(self.seed if seed is None else seed)
        text = self.apply_text_rules(text, rng)

        font = self.patched_font
        rtl = is_rtl(text, self.shape_options)
        lines = [self.shape_line(line, font, rtl=rtl, rng=rng) for line in text.split("\n")]
        ink = rasterize(lines, self.layout, rtl=rtl, rng=rng)
        for effect in self.effects:
            ink = effect.apply(ink, rng)
        return ink

    def shape_line(self, line: str, font: Font, *, rtl: bool, rng: np.random.Generator) -> list[ShapedGlyph]:
        glyphs = shape(line, font, self.shape_options, fallbacks=self._fallback_fonts)
        if not self.glyph_rules:
            return glyphs
        ctx = LineContext(
            text=line,
            font=font,
            layout=self.layout,
            options=self.shape_options,
            rtl=rtl,
            fallbacks=self._fallback_fonts,
        )
        for rule in self.glyph_rules:
            glyphs = list(rule.apply(glyphs, ctx, rng))
        return glyphs

    def apply_text_rules(self, text: str, rng: np.random.Generator | None = None) -> str:
        rng = rng if rng is not None else np.random.default_rng(self.seed)
        for rule in self.text_rules:
            text = rule.apply(text, rng)
        return text


def render(
    text: str,
    font: FontLike,
    *,
    size: float = 64.0,
    tracking: float = 0.0,
    padding: int = 40,
    patches: Sequence[FontPatch] = (),
    glyph_rules: Sequence[GlyphRule] = (),
    effects: Sequence[Effect] = (),
    text_rules: Sequence[TextRule] = (),
    fallbacks: Sequence[FontLike] = (),
    foreground: tuple[int, int, int] | str = "black",
    background: tuple[int, int, int] | str = "white",
    mode: str = "L",
    seed: int | None = None,
) -> Image.Image:
    synth = Synthesizer(
        font=font,
        layout=Layout(size=size, tracking=tracking, padding=padding),
        font_patches=patches,
        glyph_rules=glyph_rules,
        effects=effects,
        text_rules=text_rules,
        fallbacks=fallbacks,
        foreground=foreground,
        background=background,
        mode=mode,
        seed=seed,
    )
    return synth(text)
