from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont

from .fonts import Font, FontLike
from .glyphs import Outline
from .outlines import (
    Contour,
    classify_contours,
    draw_contours,
    find_stretch_cut,
    glyph_contours,
    outline_bounds,
    stretch_x,
    translate_contour,
)
from .patching import (
    ALL_CONTEXTS,
    add_gsub_lookup,
    inject_glyph,
    probe_options,
    shaped_sequences,
)
from .shaping import is_rtl

TATWEEL = "ـ"

JOINS_FORWARD = "يئهشسقفغعضصنمكظطخحجثتب" + "پچکگݢڠڽڤیۆھڭٿٹڎډ" + TATWEEL

JOINS_BACKWARD = JOINS_FORWARD + "لدرااوژڑۏذزةى"

ELONGATABLE = JOINS_FORWARD.replace(TATWEEL, "")

_WORD = re.compile(r"[؀-ۿݐ-ݿࡰ-࢟ࢠ-ࣿ]+")


@dataclass
class Kashida:
    frequency: int | tuple[int, int] = 3
    contrast: float = 0.8
    probability: float = 1.0
    min_length: int = 0
    joins_forward: str = JOINS_FORWARD
    joins_backward: str = JOINS_BACKWARD

    def apply(self, text: str, rng: np.random.Generator) -> str:
        text = strip_kashida(text)
        pattern = re.compile(f"[{re.escape(self.joins_forward)}][{re.escape(self.joins_backward)}]")

        def elongate(match: re.Match[str]) -> str:
            word = match.group(0)
            if len(word) < self.min_length:
                return word
            if self.probability < 1.0 and rng.random() >= self.probability:
                return word
            sites = _sites(word, pattern)
            if not sites:
                return word
            budget = self._budget(rng)
            out = word
            added = 0
            for site, count in zip(sites, distribute(budget, len(sites), self.contrast)):
                if count <= 0:
                    continue
                at = site + 1 + added
                out = out[:at] + TATWEEL * count + out[at:]
                added += count
            return out

        return _WORD.sub(elongate, text)

    def _budget(self, rng: np.random.Generator) -> int:
        if isinstance(self.frequency, tuple):
            low, high = self.frequency
            return int(rng.integers(low, high + 1))
        return int(self.frequency)


def strip_kashida(text: str) -> str:
    return text.replace(TATWEEL, "")


def _sites(word: str, pattern: re.Pattern[str]) -> list[int]:
    sites: list[int] = []
    start = 0
    while True:
        match = pattern.search(word, start)
        if not match:
            return sites
        sites.append(match.start())
        start = match.start() + 1


def distribute(budget: int, sites: int, contrast: float) -> list[int]:
    if sites <= 0 or budget <= 0:
        return [0] * max(sites, 0)
    if contrast <= 0.0:
        return [_round_half_up(budget / sites)] * sites
    if contrast >= 1.0:
        return [budget] + [0] * (sites - 1)

    flat = budget / sites
    first = flat + (budget - flat) * contrast
    slope = first * first / budget
    return [max(_round_half_up(first - slope * i), 0) for i in range(sites)]


def _round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


@dataclass
class ElongatedForm:
    font: FontLike
    parts: Sequence[str]
    dot_shift: float = 0.5
    mark_size: float = 0.3
    elongation: float | None = None
    """The length of the extension.

    The default is the sum of the advances of the parts that are not the
    letter.
    """
    tt: TTFont | None = None
    """A fontTools view of ``font`` to read. Callers can share one view."""

    def __post_init__(self) -> None:
        self._analysis: dict[str, Any] | None = None

    def analyse(self) -> dict[str, Any]:
        if self._analysis is None:
            source = Font.load(self.font)
            tt = self.tt if self.tt is not None else source.ttfont()
            glyph_set = tt.getGlyphSet()
            placed = []
            x = 0.0
            for name in self.parts:
                contours = glyph_contours(glyph_set, name)
                placed.append({
                    "name": name,
                    "x": x,
                    "contours": contours,
                    "parts": classify_contours(contours, source.upem, mark_size=self.mark_size),
                    "advance": float(tt["hmtx"][name][0]),
                })
                x += placed[-1]["advance"]
            self._analysis = {"placed": placed, "advance": x, "upem": source.upem}
        return self._analysis

    @property
    def carries_marks(self) -> bool:
        return any(p["parts"].has_marks for p in self.analyse()["placed"])

    def build(self, target_upem: int) -> Outline:
        analysis = self.analyse()
        scale = target_upem / analysis["upem"]
        placed = analysis["placed"]
        letter = next((p for p in placed if p["parts"].has_marks), None)

        contours: list[Contour] = []
        for part in placed:
            marks = set(part["parts"].marks)
            shift = self._mark_shift(placed, part) if part is letter else 0.0
            for i, contour in enumerate(part["contours"]):
                dx = part["x"] + (shift if i in marks else 0.0)
                contours.append(translate_contour(contour, dx, 0.0))

        if scale != 1.0:
            contours = [_scale_contour(c, scale) for c in contours]

        advance = analysis["advance"] * scale

        def draw(pen: Any) -> None:
            draw_contours(pen, contours)

        return Outline(draw, advance)

    def _mark_shift(self, placed: Sequence[dict[str, Any]], letter: dict[str, Any]) -> float:
        if self.elongation is not None:
            return -self.dot_shift * self.elongation
        before = sum(p["advance"] for p in placed if p["x"] < letter["x"])
        after = sum(p["advance"] for p in placed if p["x"] > letter["x"])
        return self.dot_shift * (after - before)


@dataclass
class StretchedForm:
    font: FontLike
    glyph: str
    amount: float
    """The length of the extension, in font units."""
    dot_shift: float = 0.5
    mark_size: float = 0.3
    side: str = "left"
    """The end of the letter that receives the extension."""
    tt: TTFont | None = None

    def __post_init__(self) -> None:
        self._analysis: dict[str, Any] | None = None

    def analyse(self) -> dict[str, Any]:
        if self._analysis is None:
            source = Font.load(self.font)
            tt = self.tt if self.tt is not None else source.ttfont()
            contours = glyph_contours(tt.getGlyphSet(), self.glyph)
            parts = classify_contours(contours, source.upem, mark_size=self.mark_size)
            body = [contours[i] for i in range(len(contours)) if i not in parts.marks]
            self._analysis = {
                "contours": contours,
                "parts": parts,
                "cut": find_stretch_cut(body, near=self.side),
                "advance": float(tt["hmtx"][self.glyph][0]),
                "upem": source.upem,
            }
        return self._analysis

    def stretchable(self) -> bool:
        return self.analyse()["cut"] is not None

    def build(self, target_upem: int) -> Outline:
        analysis = self.analyse()
        cut = analysis["cut"]
        if cut is None:
            raise ValueError(f"{self.glyph!r} has no flat stroke to stretch")
        parts = analysis["parts"]
        marks = set(parts.marks)

        body = [c for i, c in enumerate(analysis["contours"]) if i not in marks]
        contours = stretch_x(body, cut, self.amount)

        for i in sorted(marks):
            contour = analysis["contours"][i]
            bounds = outline_bounds([contour])
            centre = (bounds[0] + bounds[2]) / 2.0 if bounds else 0.0
            carried = self.amount if centre > cut else 0.0
            contours.append(translate_contour(contour, carried - self.dot_shift * self.amount, 0.0))

        scale = target_upem / analysis["upem"]
        if scale != 1.0:
            contours = [_scale_contour(c, scale) for c in contours]
        advance = (analysis["advance"] + self.amount) * scale

        def draw(pen: Any) -> None:
            draw_contours(pen, contours)

        return Outline(draw, advance)


def _scale_contour(contour: Contour, scale: float) -> Contour:
    out: Contour = []
    for op, args in contour:
        if op in ("moveTo", "lineTo", "curveTo", "qCurveTo"):
            out.append((
                op,
                tuple(None if p is None else (p[0] * scale, p[1] * scale) for p in args),
            ))
        else:
            out.append((op, args))
    return out


@dataclass
class KashidaForms:
    letters: str = ELONGATABLE
    max_run: int = 4
    dot_shift: float = 0.5
    """The fraction of the extension that the dots move. A value of 0.5 centres them."""
    contexts: Sequence[str] = ALL_CONTEXTS
    feature: str = "rlig"
    mark_size: float = 0.3
    synthetic_step: float = 0.22
    """The extension for each tatweel, in ems, for a font with no tatweel glyph."""

    built: list[str] = field(default_factory=list, init=False)
    """The names of the glyphs that the last :meth:`apply` call injected."""

    def apply(self, tt: TTFont, source: Font) -> None:
        options = probe_options(self.feature)
        order = source.glyph_order
        view = source.ttfont()
        rtl = is_rtl(self.letters[:1] or "ب", options)
        has_tatweel = source.covers(TATWEEL)

        singles: dict[str, str] = {}
        ligatures: dict[tuple[str, ...], str] = {}
        self.built = []

        for letter in dict.fromkeys(self.letters):
            if not source.covers(letter):
                continue
            base = shaped_sequences(source, letter, contexts=self.contexts, options=options)
            for run in range(1, self.max_run + 1):
                text = letter + TATWEEL * run
                sequences = shaped_sequences(source, text, contexts=self.contexts, options=options)
                for context, gids in sequences.items():
                    names = tuple(order[gid] for gid in gids)
                    if names in ligatures or (len(names) == 1 and names[0] in singles):
                        continue
                    glyph = self._form(
                        source,
                        names,
                        rtl=rtl,
                        run=run,
                        base=base.get(context),
                        order=order,
                        has_tatweel=has_tatweel,
                        view=view,
                    )
                    if glyph is None:
                        continue
                    injected = inject_glyph(tt, f"fm.kashida.{_slug(letter)}.{run}", glyph)
                    self.built.append(injected)
                    if len(names) == 1:
                        singles[names[0]] = injected
                    else:
                        ligatures[names] = injected

        for lookup in _lookups(singles, ligatures):
            add_gsub_lookup(tt, lookup, self.feature)

    def _form(
        self,
        source: Font,
        names: tuple[str, ...],
        *,
        rtl: bool,
        run: int,
        base: tuple[int, ...] | None,
        order: Sequence[str],
        has_tatweel: bool,
        view: TTFont,
    ) -> ElongatedForm | StretchedForm | None:
        if not has_tatweel:
            letter = names[0] if not rtl else names[-1]
            form = StretchedForm(
                source,
                letter,
                amount=self.synthetic_step * run * source.upem,
                dot_shift=self.dot_shift,
                mark_size=self.mark_size,
                tt=view,
            )
            marks = form.analyse()["parts"].has_marks
            return form if marks and form.stretchable() else None

        visual = tuple(reversed(names)) if rtl else names
        elongation = None
        if len(names) == 1:
            if not base or len(base) != 1:
                return None
            widths = view["hmtx"]
            elongation = float(widths[names[0]][0] - widths[order[base[0]]][0])
            if elongation <= 0:
                return None
        form = ElongatedForm(
            source,
            visual,
            dot_shift=self.dot_shift,
            mark_size=self.mark_size,
            elongation=elongation,
            tt=view,
        )
        return form if form.carries_marks else None


def _lookups(singles: dict[str, str], ligatures: dict[tuple[str, ...], str]) -> list[Any]:
    lookups = []
    if singles:
        lookups.append(otl.buildLookup([otl.buildSingleSubstSubtable(singles)]))
    if ligatures:
        lookups.append(otl.buildLookup([otl.buildLigatureSubstSubtable(ligatures)]))
    return lookups


def _slug(text: str) -> str:
    return "".join(f"{ord(c):04x}" for c in text)


__all__ = [
    "ELONGATABLE",
    "ElongatedForm",
    "JOINS_BACKWARD",
    "JOINS_FORWARD",
    "Kashida",
    "KashidaForms",
    "StretchedForm",
    "TATWEEL",
    "distribute",
    "strip_kashida",
]
