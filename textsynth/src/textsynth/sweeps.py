from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass, field, replace
from typing import Any, Iterator, Sequence

import numpy as np
from fontTools.ttLib import TTFont

from .fonts import Font, FontLike
from .glyphrules import LineContext
from .glyphs import Outline

from .kashida import JOINS_BACKWARD, JOINS_FORWARD
from .outlines import (
    Contour,
    Nib,
    Path,
    Point,
    StrokeEnd,
    TailCut,
    body_path,
    classify_contours,
    contour_area,
    cut_terminal,
    draw_contours,
    glyph_contours,
    measure_end,
    offset_edges,
)
from .patching import AddGlyph, FontPatch, inject_glyph, patch_font, shaped_sequences
from .shaping import ShapedGlyph

SWEEPERS = "ورزژۏؤڑۆ"

REVERSE_SWEEPERS = "جحخچعغڠے"


@dataclass
class SweepShape:
    belly: float = 0.7
    """The position of the lowest point, as a fraction of the sweep length.

    This class solves for this value, not for a depth. An exact
    continuation of the waw of the Amiri font gives a flat sweep, because
    that tail is already level at its end. Thus the class must find the
    arc. A depth setting does not control the stroke at its end: the
    stroke can still go down when it stops. A position for the lowest
    point controls the full shape. The depth is then a result of the
    length, which is correct. A longer sweep goes deeper.
    """
    max_depth: float = 0.55
    """The maximum depth, in ems. It limits a very long sweep."""
    ease: float = 0.03
    """The distance, in ems, in which the arc replaces the letter curvature.

    This distance is short. A terminal that leaves a bowl turns too
    tightly to continue for long. The waw of the Amiri font has a radius
    of less than one fifth of an em. Thus this class mixes the two
    curvatures. It does not continue the letter curvature at full
    strength. This mix makes the join G2, because the sweep starts at the
    curvature of the letter.
    """
    lift: float = 0.35
    """The fraction of the width that the stroke keeps at the tip.

    This value is only the lift of the pen off the page. The nib makes the
    other changes in width, and the direction of the stroke controls them.
    """
    lift_start: float = 0.72
    """The position along the sweep where the pen starts to leave the page."""
    descender: float = 0.05
    """The minimum depth below the baseline at which a terminal can sweep.

    A sweep is a descender. In the Amiri font, dal, tah, and an isolated
    beh all end on the baseline. A sweep from one of them goes through the
    word, not below it.
    """
    cut_back: float = 0.26
    """The distance back along the terminal at which the cut occurs, in ems.

    The distance must be large enough that the stroke still moves at the
    cut. A cut of a waw at 0.16 em is too near the tip. The tail is
    already level there: it goes at 181 degrees and has almost no
    curvature. Thus there is no motion to continue.
    """
    overlap: float = 0.025
    """The distance that a separate sweep goes back into the letter, in ems.

    A merged sweep does not need this distance, because it is the same
    outline as the letter. A sweep that is its own glyph only touches the
    letter at one edge. Anti-aliasing makes such an edge a thin line.
    Thus this class gives the sweep a small tab below the letter.
    """
    nib_angle: float | None = 135.0
    """The angle of the pen, in degrees. A value of ``None`` fits the angle.

    The classical rhombic-dot angle is 135 degrees, and it is the default.
    A fit is only as good as the stroke that it reads. On the part of the
    ra of the Amiri font that has a constant width, the fit gives 136
    degrees. But the waw tail becomes thinner from the cut to the tip, and
    no part of it is at full width. The fit then explains that decrease as
    a turn of the pen.
    """
    width: float | None = None
    """The width at the join, in ems. Give a value here to replace the measurement."""
    samples: int = 96

    def walk(
        self,
        end: StrokeEnd,
        reach: float,
        upem: float,
        arc: float,
        samples: int | None = None,
    ) -> tuple[list[Point], list[float]]:
        n = samples or max(self.samples, 16)
        step = reach / n
        ease = max(self.ease * upem, 1e-6)
        travel = end.heading

        def heading_at(s: float) -> float:
            return end.heading + end.curvature * ease * (1.0 - math.exp(-s / ease)) + arc * s

        points = [end.point]
        headings = [end.heading]
        x, y = end.point
        for i in range(4 * n):
            middle = heading_at((i + 0.5) * step)
            if abs(_wrap(middle - travel)) > math.pi / 2.0:
                break
            x += math.cos(middle) * step
            y += math.sin(middle) * step
            points.append((x, y))
            headings.append(heading_at((i + 1) * step))
            if abs(x - end.point[0]) >= reach:
                break
        return points, headings

    def solve_arc(self, end: StrokeEnd, reach: float, upem: float, direction: int) -> float:

        def profile(arc: float) -> tuple[float, float]:
            points, _ = self.walk(end, reach, upem, arc, samples=min(self.samples, 96))
            lowest = min(range(len(points)), key=lambda i: points[i][1])
            return lowest / max(len(points) - 1, 1), points[lowest][1]

        low, high = 0.0, direction * 0.02
        if profile(0.0)[0] < self.belly:
            return 0.0
        for _ in range(20):
            middle = (low + high) / 2.0
            if profile(middle)[0] > self.belly:
                low = middle
            else:
                high = middle
        arc = (low + high) / 2.0

        floor = -self.max_depth * upem
        if profile(arc)[1] >= floor:
            return arc
        low, high = arc, direction * 0.02
        for _ in range(14):
            middle = (low + high) / 2.0
            if profile(middle)[1] < floor:
                low = middle
            else:
                high = middle
        return (low + high) / 2.0

    def centreline(self, end: StrokeEnd, reach: float, upem: float, direction: int) -> tuple[list[Point], list[float]]:
        return self.walk(end, reach, upem, self.solve_arc(end, reach, upem, direction))

    def pen(self, end: StrokeEnd, upem: float, mirror: bool = False) -> Nib:
        if self.nib_angle is not None:
            angle = math.radians(self.nib_angle)
            if mirror:
                angle = math.pi - angle
        elif end.nib is not None:
            angle = end.nib.angle
        else:
            angle = end.heading - math.pi / 2.0
        joint = self.width * upem if self.width is not None else end.width
        return Nib(joint, angle).scaled_to(joint, end.heading)

    def widths(
        self,
        end: StrokeEnd,
        headings: Sequence[float],
        upem: float,
        mirror: bool = False,
    ) -> list[float]:
        nib = self.pen(end, upem, mirror)
        floor = 0.004 * upem
        out = []
        for i, heading in enumerate(headings):
            u = i / max(len(headings) - 1, 1)
            out.append(max(nib.thickness(heading) * self._lift(u), floor))
        return out

    def _lift(self, u: float) -> float:
        if u <= self.lift_start:
            return 1.0
        t = (u - self.lift_start) / max(1.0 - self.lift_start, 1e-6)
        return 1.0 - (1.0 - self.lift) * (t * t * (3.0 - 2.0 * t))


def _wrap(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def sweep_edges(
    cut: TailCut,
    end: StrokeEnd,
    shape: SweepShape,
    reach: float,
    upem: float,
    direction: int,
    mirror: bool = False,
) -> tuple[list[Point], list[Point]]:
    points, headings = shape.centreline(end, reach, upem, direction)
    left, right = offset_edges(points, shape.widths(end, headings, upem, mirror))

    normal = (-math.sin(end.heading), math.cos(end.heading))
    towards_a = (cut.a[0] - cut.centre[0]) * normal[0] + (cut.a[1] - cut.centre[1]) * normal[1]
    out_edge, back_edge = (left, right) if towards_a > 0 else (right, left)
    out_edge[0], back_edge[0] = cut.a, cut.b
    return out_edge, back_edge


def close_wound(cut: TailCut) -> Contour:
    segments = [*cut.rest.segments, ("line", (cut.rest.start,))]
    return Path(cut.rest.start, segments, closed=True).to_contour()


def detached_sweep(
    cut: TailCut,
    end: StrokeEnd,
    shape: SweepShape,
    reach: float,
    upem: float,
    *,
    direction: int = -1,
    mirror: bool = False,
) -> Contour:
    out_edge, back_edge = sweep_edges(cut, end, shape, reach, upem, direction, mirror)
    tab = shape.overlap * upem
    back_into_letter = (-math.cos(end.heading) * tab, -math.sin(end.heading) * tab)
    lip_a = (cut.a[0] + back_into_letter[0], cut.a[1] + back_into_letter[1])
    lip_b = (cut.b[0] + back_into_letter[0], cut.b[1] + back_into_letter[1])
    boundary = [cut.a, *out_edge[1:], *reversed(back_edge), lip_b]
    return [
        ("moveTo", (lip_a,)),
        *(("lineTo", (p,)) for p in boundary),
        ("closePath", ()),
    ]


def continue_stroke(
    cut: TailCut,
    end: StrokeEnd,
    shape: SweepShape,
    reach: float,
    upem: float,
    *,
    direction: int = -1,
    mirror: bool = False,
) -> Contour:
    out_edge, back_edge = sweep_edges(cut, end, shape, reach, upem, direction, mirror)
    boundary = [*out_edge[1:], *reversed(back_edge)]
    segments = [*cut.rest.segments, *(("line", (p,)) for p in boundary)]
    return Path(cut.rest.start, segments, closed=True).to_contour()


@dataclass
class _Swept:
    font: FontLike
    glyph: str
    shape: SweepShape
    direction: int = -1
    tt: TTFont | None = None
    mirror: bool = False
    """Tell the nib that the script goes to the right.

    This value comes from the script, not from ``direction``.
    """

    def __post_init__(self) -> None:
        self._read: dict[str, Any] | None = None

    def read(self) -> dict[str, Any]:
        if self._read is None:
            source = Font.load(self.font)
            tt = self.tt if self.tt is not None else source.ttfont()
            contours = glyph_contours(tt.getGlyphSet(), self.glyph)
            parts = classify_contours(contours, source.upem)
            cut = self._cut(contours, source.upem)
            self._read = {
                "contours": contours,
                "winding": parts.winding(contours),
                "cut": cut,
                "end": (
                    measure_end(
                        cut,
                        direction=self.direction,
                        max_height=-self.shape.descender * source.upem,
                    )
                    if cut is not None
                    else None
                ),
                "advance": float(tt["hmtx"][self.glyph][0]),
                "upem": source.upem,
            }
        return self._read

    def _cut(self, contours: Sequence[Contour], upem: float) -> TailCut | None:
        path = body_path(contours)
        if path is None:
            return None
        return cut_terminal(path, self.shape.cut_back * upem, direction=self.direction)

    @property
    def cut(self) -> TailCut | None:
        return self.read()["cut"]

    @property
    def end(self) -> StrokeEnd | None:
        return self.read()["end"]


@dataclass
class SweptGlyph(_Swept):
    reach: float = 0.0
    """The length of the sweep, in font units."""

    def build(self, target_upem: int) -> Outline:
        read = self.read()
        scale = target_upem / read["upem"]
        contours = self.contours()
        if scale != 1.0:
            contours = [_scaled(c, scale) for c in contours]
        advance = read["advance"] * scale

        def draw(pen: Any) -> None:
            draw_contours(pen, contours)

        return Outline(draw, advance)

    def contours(self) -> list[Contour]:
        read = self.read()
        cut = read["cut"]
        if cut is None or read["end"] is None or self.reach <= 0:
            return list(read["contours"])
        swept = continue_stroke(
            cut,
            read["end"],
            self.shape,
            self.reach,
            read["upem"],
            direction=self.direction,
            mirror=self.mirror,
        )
        body = max(read["contours"], key=lambda c: abs(contour_area(c)))
        return [swept if c is body else c for c in read["contours"]]


@dataclass
class CutGlyph(_Swept):
    def build(self, target_upem: int) -> Outline:
        read = self.read()
        cut = read["cut"]
        contours = list(read["contours"])
        if cut is not None:
            body = max(contours, key=lambda c: abs(contour_area(c)))
            contours = [close_wound(cut) if c is body else c for c in contours]
        scale = target_upem / read["upem"]
        if scale != 1.0:
            contours = [_scaled(c, scale) for c in contours]

        def draw(pen: Any) -> None:
            draw_contours(pen, contours)

        return Outline(draw, read["advance"] * scale)


@dataclass
class TailGlyph(_Swept):
    def build(self, target_upem: int) -> Outline:
        read = self.read()
        cut, end = read["cut"], read["end"]
        if cut is None or end is None:
            raise ValueError(f"{self.glyph!r} has no terminal to sweep from")
        scale = target_upem / read["upem"]
        sweep = detached_sweep(
            cut,
            end,
            self.shape,
            read["upem"],
            read["upem"],
            direction=self.direction,
            mirror=self.mirror,
        )
        contours = [_scaled(sweep, scale, dx=-cut.centre[0])]

        def draw(pen: Any) -> None:
            draw_contours(pen, contours)

        return Outline(draw, 0.0)


def _scaled(contour: Contour, scale: float, *, dx: float = 0.0) -> Contour:
    out: Contour = []
    for op, args in contour:
        if op in ("moveTo", "lineTo", "curveTo", "qCurveTo"):
            out.append((
                op,
                tuple(None if p is None else ((p[0] + dx) * scale, p[1] * scale) for p in args),
            ))
        else:
            out.append((op, args))
    return out


@dataclass(frozen=True)
class Site:
    index: int
    """The position of the letter in the shaped line, in visual order."""
    cluster: int
    length: int
    """The number of letters that the sweep must cover."""
    reach: float
    """The width of those letters, in the font units of the letter."""
    covered: tuple[int, ...]
    """The glyphs below which the sweep goes, also in visual order."""
    direction: int = -1
    """The way this sweep travels. A value of ``-1`` is to the left."""
    reverse: bool = False
    """Tell if this sweep goes against the way the script goes.

    The sign of ``direction`` alone does not tell you this. A forward
    sweep travels to the left in a right-to-left line and to the right in
    a left-to-right line. This value is the comparison of the two.
    """


@dataclass
class Tadakhul:
    letters: str = SWEEPERS
    reverse_letters: str = ""
    length: int | tuple[int, int] = 2
    probability: float = 1.0
    lift: float = 0.10
    max_sites: int | None = None
    shape: SweepShape = field(default_factory=SweepShape)

    def patches(self) -> Sequence[FontPatch]:
        return ()

    def sites(self, glyphs: Sequence[ShapedGlyph], ctx: LineContext, rng: np.random.Generator) -> list[Site]:
        found: list[Site] = []
        for index, glyph in enumerate(glyphs):
            if self.max_sites is not None and len(found) >= self.max_sites:
                break
            if not glyph.x_advance:
                continue
            if not (0 <= glyph.cluster < len(ctx.text)):
                continue
            letter = ctx.text[glyph.cluster]
            if letter in self.letters:
                reverse = False
            elif letter in self.reverse_letters:
                reverse = True
            else:
                continue
            if not free_after(ctx.text, glyph.cluster):
                continue
            if self.probability < 1.0 and rng.random() >= self.probability:
                continue
            site = self._measure(glyphs, ctx, index, self._length(rng), reverse)
            if site is None:
                continue
            found.append(site)
        return found

    def _length(self, rng: np.random.Generator) -> int:
        if isinstance(self.length, tuple):
            low, high = self.length
            return int(rng.integers(low, high + 1))
        return int(self.length)

    def _measure(
        self,
        glyphs: Sequence[ShapedGlyph],
        ctx: LineContext,
        index: int,
        length: int,
        reverse: bool,
    ) -> Site | None:
        glyph = glyphs[index]
        forward = -1 if ctx.rtl else 1
        direction = -forward if reverse else forward
        if not reverse:
            low = glyph.cluster
            high = _letters_after(ctx.text, glyph.cluster, max(length, 1))
            if high <= glyph.cluster + 1:
                return None
        else:
            low = _letters_before(ctx.text, glyph.cluster, max(length, 1)) - 1
            high = glyph.cluster
            if low >= glyph.cluster - 1:
                return None

        covered = [
            i
            for i, g in enumerate(glyphs)
            if low < g.cluster < high and ((i < index) if direction < 0 else (i > index))
        ]
        if not covered:
            return None

        tracking = ctx.units(ctx.layout.tracking, glyph.font)
        reach = sum(
            g.x_advance * glyph.font.upem / g.font.upem + tracking for g in (glyphs[i] for i in covered) if g.x_advance
        )
        if reach <= 0:
            return None
        return Site(index, glyph.cluster, length, reach, tuple(covered), direction, reverse)

    def lift_covered(self, glyphs: list[ShapedGlyph], sites: Sequence[Site]) -> list[ShapedGlyph]:
        if not self.lift:
            return glyphs
        rise: dict[int, int] = {}
        for site in sites:
            if site.reverse:
                continue
            for i in site.covered:
                rise[i] = rise.get(i, 0) + 1
        for i, count in rise.items():
            glyph = glyphs[i]
            glyphs[i] = replace(glyph, y_offset=glyph.y_offset + count * self.lift * glyph.font.upem)
        return glyphs


def free_after(
    text: str,
    index: int,
    *,
    joins_forward: str = JOINS_FORWARD,
    joins_backward: str = JOINS_BACKWARD,
) -> bool:
    if index >= len(text):
        return False
    if text[index] not in joins_forward:
        return True
    following = index + 1
    while following < len(text) and unicodedata.category(text[following]) == "Mn":
        following += 1
    return following >= len(text) or text[following] not in joins_backward


def _letters_after(text: str, cluster: int, count: int) -> int:
    index = cluster + 1
    seen = 0
    while index < len(text) and seen < count:
        if unicodedata.category(text[index]) != "Mn":
            seen += 1
        index += 1
    while index < len(text) and unicodedata.category(text[index]) == "Mn":
        index += 1
    return index


def _letters_before(text: str, cluster: int, count: int) -> int:
    index = cluster - 1
    seen = 0
    while index >= 0 and seen < count:
        if unicodedata.category(text[index]) != "Mn":
            seen += 1
        index -= 1
    return index + 1


@dataclass
class TadakhulMerged(Tadakhul):
    def apply(self, glyphs: Sequence[ShapedGlyph], ctx: LineContext, rng: np.random.Generator) -> list[ShapedGlyph]:
        out = list(glyphs)
        sites = self.sites(out, ctx, rng)
        if not sites:
            return out

        view = ctx.font.ttfont()
        patches: list[AddGlyph] = []
        for n, site in enumerate(sites):
            glyph = out[site.index]
            patches.append(
                AddGlyph(
                    SweptGlyph(
                        font=glyph.font,
                        glyph=glyph.name,
                        shape=self.shape,
                        direction=site.direction,
                        tt=view,
                        mirror=not ctx.rtl,
                        reach=site.reach,
                    ),
                    name=f"fm.sweep.{n}",
                )
            )
        font = patch_font(ctx.font, patches)
        for site, patch in zip(sites, patches):
            if patch.injected_gid is None:
                continue
            out[site.index] = replace(out[site.index], gid=patch.injected_gid, font=font)
        return self.lift_covered(out, sites)


def _sweeping_glyphs(
    source: Font, letters: str, reverse_letters: str, direction: int
) -> Iterator[tuple[int, str, int]]:
    seen: set[int] = set()
    order = source.glyph_order
    for group, way in ((letters, direction), (reverse_letters, -direction)):
        for letter in dict.fromkeys(group):
            if not source.covers(letter):
                continue
            for gids in shaped_sequences(source, letter).values():
                if len(gids) != 1 or gids[0] in seen:
                    continue
                seen.add(gids[0])
                yield gids[0], order[gids[0]], way


@dataclass
class SweepLadder:
    letters: str = SWEEPERS
    reverse_letters: str = ""
    """The letters that sweep the other way. See :data:`REVERSE_SWEEPERS`."""
    steps: int = 8
    min_reach: float = 0.6
    """The shortest rung, in ems."""
    max_reach: float = 5.0
    """The longest rung, in ems."""
    shape: SweepShape = field(default_factory=SweepShape)
    direction: int = -1
    """The way a letter in ``letters`` sweeps.

    A letter in ``reverse_letters`` sweeps the other way. This patch runs
    before the code reads any text, thus it cannot get the direction from
    the line. The default is the direction of a right-to-left script.
    """
    mirror: bool = False

    rungs: dict[int, list[tuple[float, int]]] = field(default_factory=dict, init=False)
    """A map from a base glyph id to a list of ``(reach, swept glyph id)``.

    The reach is in font units. This map holds ids, not names. A format 3
    ``post`` table keeps no names. Thus the name of an injected glyph does
    not stay after a save of the font.

    One glyph has rungs for one direction only. A terminal goes one way,
    thus a letter sweeps one way, and the two letter sets do not meet.
    """

    def reaches(self, upem: float) -> list[float]:
        if self.steps <= 1:
            return [self.max_reach * upem]
        span = (self.max_reach - self.min_reach) / (self.steps - 1)
        return [(self.min_reach + span * i) * upem for i in range(self.steps)]

    def apply(self, tt: TTFont, source: Font) -> None:
        self.rungs = {}
        view = source.ttfont()
        for base, name, direction in _sweeping_glyphs(source, self.letters, self.reverse_letters, self.direction):
            probe = SweptGlyph(
                font=source,
                glyph=name,
                shape=self.shape,
                direction=direction,
                tt=view,
                mirror=self.mirror,
            )
            if probe.end is None:
                continue
            rungs = []
            for i, reach in enumerate(self.reaches(source.upem)):
                swept = replace(probe, reach=reach)
                injected = inject_glyph(tt, f"fm.sweep.{name}.{i}", swept)
                rungs.append((reach, tt.getGlyphID(injected)))
            self.rungs[base] = rungs

    def nearest(self, gid: int, reach: float) -> int | None:
        rungs = self.rungs.get(gid)
        if not rungs:
            return None
        return min(rungs, key=lambda rung: abs(rung[0] - reach))[1]


@dataclass
class TadakhulQuantised(Tadakhul):
    steps: int = 8
    min_reach: float = 0.6
    max_reach: float = 5.0
    ladder: SweepLadder | None = None
    """The ladder that supplies the rungs.

    If you do not give a ladder, this class makes one from the settings above.
    """

    def __post_init__(self) -> None:
        if self.ladder is None:
            self.ladder = SweepLadder(
                letters=self.letters,
                reverse_letters=self.reverse_letters,
                steps=self.steps,
                min_reach=self.min_reach,
                max_reach=self.max_reach,
                shape=self.shape,
            )

    def patches(self) -> Sequence[FontPatch]:
        return (self.ladder,)

    def apply(self, glyphs: Sequence[ShapedGlyph], ctx: LineContext, rng: np.random.Generator) -> list[ShapedGlyph]:
        out = list(glyphs)
        sites = self.sites(out, ctx, rng)
        if not sites:
            return out
        for site in sites:
            glyph = out[site.index]
            swept = self.ladder.nearest(glyph.gid, site.reach)
            if swept is None:
                continue
            out[site.index] = replace(glyph, gid=swept)
        return self.lift_covered(out, sites)


@dataclass
class TailLadder:
    letters: str = SWEEPERS
    reverse_letters: str = ""
    """The letters that sweep the other way. See :data:`REVERSE_SWEEPERS`."""
    shape: SweepShape = field(default_factory=SweepShape)
    direction: int = -1
    """The way a letter in ``letters`` sweeps.

    A letter in ``reverse_letters`` sweeps the other way.
    """
    mirror: bool = False

    tails: dict[int, tuple[int, int, float]] = field(default_factory=dict, init=False)
    """A map from a base glyph id to ``(cut letter id, tail id, cut x)``.

    The cut x value is in font units. One glyph has one tail, because a
    terminal goes one way only.
    """

    def apply(self, tt: TTFont, source: Font) -> None:
        self.tails = {}
        view = source.ttfont()
        for base, name, direction in _sweeping_glyphs(source, self.letters, self.reverse_letters, self.direction):
            tail = TailGlyph(
                font=source,
                glyph=name,
                shape=self.shape,
                direction=direction,
                tt=view,
                mirror=self.mirror,
            )
            if tail.end is None:
                continue
            stump = CutGlyph(
                font=source,
                glyph=name,
                shape=self.shape,
                direction=direction,
                tt=view,
                mirror=self.mirror,
            )
            cut_id = tt.getGlyphID(inject_glyph(tt, f"fm.cut.{name}", stump))
            tail_id = tt.getGlyphID(inject_glyph(tt, f"fm.tail.{name}", tail))
            self.tails[base] = (cut_id, tail_id, tail.cut.centre[0])


@dataclass
class TadakhulScaled(Tadakhul):
    tails: TailLadder | None = None
    """The tails to stretch.

    If you do not give a ladder, this class makes one from ``letters`` and
    ``shape``.
    """

    def __post_init__(self) -> None:
        if self.tails is None:
            self.tails = TailLadder(
                letters=self.letters,
                reverse_letters=self.reverse_letters,
                shape=self.shape,
            )

    def patches(self) -> Sequence[FontPatch]:
        return (self.tails,)

    def apply(self, glyphs: Sequence[ShapedGlyph], ctx: LineContext, rng: np.random.Generator) -> list[ShapedGlyph]:
        out = list(glyphs)
        sites = self.sites(out, ctx, rng)
        if not sites:
            return out
        out = self.lift_covered(out, sites)

        for site in sorted(sites, key=lambda s: s.index, reverse=True):
            glyph = out[site.index]
            entry = self.tails.tails.get(glyph.gid)
            if entry is None:
                continue
            stump, tail, wound = entry
            out[site.index] = replace(glyph, gid=stump)
            out.insert(
                site.index + 1,
                ShapedGlyph(
                    gid=tail,
                    cluster=glyph.cluster,
                    x_advance=0.0,
                    y_advance=0.0,
                    x_offset=wound - glyph.x_advance,
                    y_offset=glyph.y_offset,
                    font=glyph.font,
                    x_scale=site.reach / glyph.font.upem,
                ),
            )
        return out


__all__ = [
    "REVERSE_SWEEPERS",
    "SWEEPERS",
    "Site",
    "SweepLadder",
    "SweepShape",
    "SweptGlyph",
    "free_after",
    "CutGlyph",
    "Tadakhul",
    "TadakhulMerged",
    "TadakhulQuantised",
    "TadakhulScaled",
    "TailGlyph",
    "TailLadder",
]
