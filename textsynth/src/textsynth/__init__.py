from __future__ import annotations

from . import effects, kashida, outlines, sweeps, textrules
from .effects import (
    Blobify,
    Blot,
    Blur,
    ComponentFilter,
    Effect,
    Erode,
    InkBleed,
    Pipeline,
    Smudge,
    Speckle,
    Threshold,
    Warp,
)
from .fonts import Font
from .glyphrules import GlyphRule, LineContext
from .outlines import Nib, StrokeEnd, TailCut
from .glyphs import BorrowedGlyph, CompositeGlyph, GlyphSource, Outline, PenGlyph, SVGGlyph
from .kashida import ElongatedForm, Kashida, KashidaForms, StretchedForm
from .layout import Layout
from .patching import (
    AddGlyph,
    FontPatch,
    GlyphSubstitution,
    patch_font,
    shaped_sequences,
)
from .raster import image_to_ink, ink_to_image, rasterize
from .shaping import ShapedGlyph, ShapeOptions, shape
from .sweeps import (
    REVERSE_SWEEPERS,
    SWEEPERS,
    CutGlyph,
    SweepLadder,
    SweepShape,
    SweptGlyph,
    Tadakhul,
    TadakhulMerged,
    TadakhulQuantised,
    TadakhulScaled,
    TailGlyph,
    TailLadder,
)
from .synth import Synthesizer, render
from .textrules import (
    Callback,
    Drop,
    Regex,
    RuleSet,
    Substitute,
    Swap,
    TextRule,
    orthographic_variation,
)

__version__ = "0.2.0"

__all__ = [
    "AddGlyph",
    "Blobify",
    "Blot",
    "Blur",
    "BorrowedGlyph",
    "Callback",
    "ComponentFilter",
    "CompositeGlyph",
    "CutGlyph",
    "Drop",
    "Effect",
    "ElongatedForm",
    "Erode",
    "Font",
    "FontPatch",
    "GlyphRule",
    "GlyphSource",
    "GlyphSubstitution",
    "InkBleed",
    "Kashida",
    "KashidaForms",
    "Layout",
    "Nib",
    "LineContext",
    "Outline",
    "PenGlyph",
    "Pipeline",
    "Regex",
    "RuleSet",
    "SVGGlyph",
    "ShapeOptions",
    "ShapedGlyph",
    "Smudge",
    "Speckle",
    "StrokeEnd",
    "StretchedForm",
    "Substitute",
    "SWEEPERS",
    "REVERSE_SWEEPERS",
    "SweepLadder",
    "SweepShape",
    "SweptGlyph",
    "Synthesizer",
    "TailCut",
    "Swap",
    "Tadakhul",
    "TadakhulMerged",
    "TadakhulQuantised",
    "TadakhulScaled",
    "TailGlyph",
    "TailLadder",
    "TextRule",
    "Threshold",
    "Warp",
    "effects",
    "image_to_ink",
    "ink_to_image",
    "kashida",
    "orthographic_variation",
    "outlines",
    "patch_font",
    "rasterize",
    "render",
    "shape",
    "shaped_sequences",
    "sweeps",
    "textrules",
]
