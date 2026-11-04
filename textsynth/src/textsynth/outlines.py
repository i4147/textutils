from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from fontTools.pens.recordingPen import DecomposingRecordingPen

Point = tuple[float, float]
Segment = tuple[str, tuple]
Contour = list[Segment]

_DRAW_OPS = ("moveTo", "lineTo", "curveTo", "qCurveTo")
_END_OPS = ("closePath", "endPath")


def glyph_contours(glyph_set: Any, name: str) -> list[Contour]:
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(pen)
    return split_contours(pen.value)


def split_contours(recording: Sequence[Segment]) -> list[Contour]:
    contours: list[Contour] = []
    current: Contour = []
    for op, args in recording:
        if op in _DRAW_OPS:
            current.append((op, args))
        elif op in _END_OPS:
            if current:
                current.append((op, args))
                contours.append(current)
            current = []
    if current:
        contours.append(current)
    return contours


def contour_points(contour: Contour) -> list[Point]:
    return [p for _, args in contour for p in args if p is not None]


def contour_area(contour: Contour) -> float:
    points = contour_points(contour)
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def contour_bounds(contour: Contour) -> tuple[float, float, float, float] | None:
    points = contour_points(contour)
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def outline_bounds(
    contours: Iterable[Contour],
) -> tuple[float, float, float, float] | None:
    boxes = [b for b in (contour_bounds(c) for c in contours) if b]
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


@dataclass(frozen=True)
class Parts:
    body: int
    marks: tuple[int, ...]
    holes: tuple[int, ...]

    @property
    def has_marks(self) -> bool:
        return bool(self.marks)

    def winding(self, contours: Sequence[Contour]) -> float:
        area = contour_area(contours[self.body]) if 0 <= self.body < len(contours) else 0.0
        return math.copysign(1.0, area) if area else 1.0


def classify_contours(
    contours: Sequence[Contour],
    upem: float,
    *,
    mark_size: float = 0.3,
    mark_aspect: float = 2.2,
) -> Parts:
    if not contours:
        return Parts(-1, (), ())
    areas = [contour_area(c) for c in contours]
    body = max(range(len(contours)), key=lambda i: abs(areas[i]))
    outer = math.copysign(1.0, areas[body]) if areas[body] else 1.0
    limit = mark_size * upem

    marks: list[int] = []
    holes: list[int] = []
    for i, area in enumerate(areas):
        if i == body:
            continue
        if area and math.copysign(1.0, area) != outer:
            holes.append(i)
            continue
        box = contour_bounds(contours[i])
        if not box:
            continue
        w, h = box[2] - box[0], box[3] - box[1]
        if max(w, h) <= limit and max(w, h) <= mark_aspect * max(min(w, h), 1e-9):
            marks.append(i)
    return Parts(body, tuple(marks), tuple(holes))


def translate_contour(contour: Contour, dx: float, dy: float) -> Contour:
    if not dx and not dy:
        return list(contour)
    moved: Contour = []
    for op, args in contour:
        if op in _DRAW_OPS:
            moved.append((op, tuple(None if p is None else (p[0] + dx, p[1] + dy) for p in args)))
        else:
            moved.append((op, args))
    return moved


def draw_contours(pen: Any, contours: Iterable[Contour]) -> None:
    for contour in contours:
        closed = False
        for op, args in contour:
            getattr(pen, op)(*args)
            closed = closed or op in _END_OPS
        if not closed:
            pen.closePath()


def stretch_x(contours: Sequence[Contour], cut: float, amount: float) -> list[Contour]:
    out: list[Contour] = []
    for contour in contours:
        moved: Contour = []
        for op, args in contour:
            if op in _DRAW_OPS:
                moved.append((
                    op,
                    tuple(None if p is None else ((p[0] + amount, p[1]) if p[0] > cut else p) for p in args),
                ))
            else:
                moved.append((op, args))
        out.append(moved)
    return out


def find_stretch_cut(
    contours: Sequence[Contour],
    *,
    near: str = "left",
    margin: float = 0.06,
    flatness: float = 0.12,
) -> float | None:
    bounds = outline_bounds(contours)
    if not bounds:
        return None
    x_min, y_min, x_max, y_max = bounds
    width = x_max - x_min
    if width <= 0:
        return None
    limit = max(flatness * (y_max - y_min), 1e-6)

    steps = 24
    inset = margin * width
    for i in range(steps):
        t = (i + 0.5) / steps
        x = (x_min + inset) + t * (width - 2 * inset)
        if near == "right":
            x = (x_max - inset) - t * (width - 2 * inset)
        if _crossings_are_flat(contours, x, limit):
            return x
    return None


def _crossings_are_flat(contours: Sequence[Contour], x: float, limit: float) -> bool:
    crossings = 0
    for contour in contours:
        start: Point | None = None
        current: Point | None = None
        for op, args in contour:
            if op == "moveTo":
                start = current = args[0]
            elif op in ("lineTo", "curveTo", "qCurveTo"):
                points = [p for p in args if p is not None]
                if not points or current is None:
                    continue
                end = points[-1]
                span = [current, *points]
                if any(_straddles(a[0], b[0], x) for a, b in zip(span, span[1:])):
                    ys = [p[1] for p in span]
                    if max(ys) - min(ys) > limit:
                        return False
                    crossings += 1
                current = end
            elif op in _END_OPS:
                if current is not None and start is not None and _straddles(current[0], start[0], x):
                    if abs(current[1] - start[1]) > limit:
                        return False
                    crossings += 1
                current = start
    return crossings == 2


def _straddles(a: float, b: float, x: float) -> bool:
    return (a < x < b) or (b < x < a)


def cubic(p0: Point, c1: Point, c2: Point, p3: Point, samples: int) -> list[Point]:
    out = []
    for i in range(samples + 1):
        t = i / samples
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def arc_lengths(points: Sequence[Point]) -> list[float]:
    total = 0.0
    lengths = [0.0]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        total += math.hypot(x2 - x1, y2 - y1)
        lengths.append(total)
    if total <= 0:
        return [0.0] * len(points)
    return [length / total for length in lengths]


def offset_edges(points: Sequence[Point], widths: Sequence[float]) -> tuple[list[Point], list[Point]]:
    normals = _normals(points)
    left: list[Point] = []
    right: list[Point] = []
    for (x, y), (nx, ny), w in zip(points, normals, widths):
        half = max(w, 0.0) / 2.0
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return left, right


def _normals(points: Sequence[Point]) -> list[Point]:
    normals: list[Point] = []
    for i in range(len(points)):
        prev = points[max(i - 1, 0)]
        nxt = points[min(i + 1, len(points) - 1)]
        dx, dy = nxt[0] - prev[0], nxt[1] - prev[1]
        length = math.hypot(dx, dy)
        if length == 0:
            normals.append((0.0, 1.0))
        else:
            normals.append((-dy / length, dx / length))
    return normals


@dataclass
class Path:
    start: Point
    segments: list[tuple[str, tuple[Point, ...]]]
    """One ``("line" | "quad" | "cubic", (controls..., end))`` for each segment."""
    closed: bool = True

    @classmethod
    def from_contour(cls, contour: Contour) -> "Path":
        from fontTools.pens.basePen import decomposeQuadraticSegment

        start: Point = (0.0, 0.0)
        segments: list[tuple[str, tuple[Point, ...]]] = []
        closed = False
        current: Point = start
        for op, args in contour:
            if op == "moveTo":
                start = current = args[0]
            elif op == "lineTo":
                segments.append(("line", (args[0],)))
                current = args[0]
            elif op == "curveTo":
                segments.append(("cubic", tuple(args)))
                current = args[-1]
            elif op == "qCurveTo":
                points = list(args)
                if points and points[-1] is None:
                    points = points[:-1]
                    if not points:
                        continue
                    implied = _midpoint(points[-1], points[0])
                    start = current = implied
                    points = [*points, implied]
                for control, end in decomposeQuadraticSegment(tuple(points)):
                    segments.append(("quad", (control, end)))
                    current = end
            elif op in _END_OPS:
                closed = True
        if closed and current != start:
            segments.append(("line", (start,)))
        return cls(start, segments, closed)

    def to_contour(self) -> Contour:
        contour: Contour = [("moveTo", (self.start,))]
        for kind, points in self.segments:
            if kind == "line":
                contour.append(("lineTo", points))
            elif kind == "quad":
                contour.append(("qCurveTo", points))
            else:
                contour.append(("curveTo", points))
        contour.append(("closePath", ()) if self.closed else ("endPath", ()))
        return contour

    def nodes(self) -> list[Point]:
        return [self.start, *(points[-1] for points in (s[1] for s in self.segments))]

    def node_count(self) -> int:
        return len(self.segments) if self.closed else len(self.segments) + 1


def _midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def sample_segment(start: Point, kind: str, points: Sequence[Point], n: int = 12) -> list[Point]:
    if kind == "line":
        return [_lerp(start, points[0], i / n) for i in range(n + 1)]
    if kind == "quad":
        control, end = points
        out = []
        for i in range(n + 1):
            t = i / n
            out.append(_lerp(_lerp(start, control, t), _lerp(control, end, t), t))
        return out
    c1, c2, end = points
    return cubic(start, c1, c2, end, n)


def segment_length(start: Point, kind: str, points: Sequence[Point]) -> float:
    samples = sample_segment(start, kind, points)
    return sum(math.dist(a, b) for a, b in zip(samples, samples[1:]))


def split_segment(
    start: Point, kind: str, points: Sequence[Point], t: float
) -> tuple[tuple[str, tuple[Point, ...]], tuple[str, tuple[Point, ...]]]:
    if kind == "line":
        mid = _lerp(start, points[0], t)
        return ("line", (mid,)), ("line", (points[0],))
    if kind == "quad":
        control, end = points
        a, b = _lerp(start, control, t), _lerp(control, end, t)
        mid = _lerp(a, b, t)
        return ("quad", (a, mid)), ("quad", (b, end))
    c1, c2, end = points
    a, b, c = _lerp(start, c1, t), _lerp(c1, c2, t), _lerp(c2, end, t)
    d, e = _lerp(a, b, t), _lerp(b, c, t)
    mid = _lerp(d, e, t)
    return ("cubic", (a, d, mid)), ("cubic", (e, c, end))


@dataclass(frozen=True)
class TailCut:
    rest: Path
    a: Point
    b: Point
    tip: Point
    tail: tuple[tuple[str, tuple[Point, ...]], ...]
    """The part that this class removed, if a caller needs it."""

    @property
    def width(self) -> float:
        return math.dist(self.a, self.b)

    @property
    def centre(self) -> Point:
        return _midpoint(self.a, self.b)


def cut_terminal(path: Path, distance: float, *, direction: int = -1, max_spread: float = 0.7) -> TailCut | None:
    nodes = path.nodes()
    count = path.node_count()
    if count < 6:
        return None
    tip = min(range(count), key=lambda i: (-direction * nodes[i][0], -nodes[i][1]))

    forward = _reach_along(path, tip, +1, distance)
    backward = _reach_along(path, tip, -1, distance)
    if forward is None or backward is None:
        return None

    a = _point_at(path, *backward)
    b = _point_at(path, *forward)
    if math.dist(a, b) > max_spread * distance:
        return None

    rest, tail = _open_between(path, backward, forward)
    return TailCut(rest=rest, a=a, b=b, tip=nodes[tip], tail=tuple(tail))


@dataclass(frozen=True)
class Nib:
    width: float
    """The full width of the nib, in font units."""
    angle: float
    """The angle of the edge of the nib, in radians."""

    def thickness(self, heading: float) -> float:
        return abs(self.width * math.sin(heading - self.angle))

    def scaled_to(self, thickness: float, heading: float) -> "Nib":
        across = abs(math.sin(heading - self.angle))
        if across < 1e-3:
            return Nib(thickness, self.angle)
        return Nib(thickness / across, self.angle)


@dataclass(frozen=True)
class StrokeEnd:
    point: Point
    heading: float
    """The direction of travel at the cut, in radians."""
    curvature: float
    """The signed curvature at the cut, in 1/units.

    A positive value is a turn counter-clockwise.
    """
    width: float
    nib: Nib | None


def tail_skeleton(cut: TailCut, samples: int = 48) -> list[tuple[Point, float]]:
    boundary = _sample_arc(cut.a, cut.tail)
    if len(boundary) < 6:
        return []
    tip = min(range(len(boundary)), key=lambda i: math.dist(boundary[i], cut.tip))
    first = _resample(boundary[: tip + 1], samples)
    second = _resample(boundary[tip:][::-1], samples)
    if not first or not second:
        return []
    return [(_midpoint(a, b), math.dist(a, b)) for a, b in zip(first, second)]


def measure_end(
    cut: TailCut,
    *,
    direction: int = -1,
    window: float = 0.25,
    max_off_axis: float = math.radians(45.0),
    max_height: float | None = None,
) -> StrokeEnd | None:
    skeleton = tail_skeleton(cut)
    if len(skeleton) < 8:
        return None
    centres = [point for point, _ in skeleton]

    span = max(int(len(centres) * window), 3)
    heading = _heading(centres[0], centres[min(span, len(centres) - 1)])
    travel = math.pi if direction < 0 else 0.0
    if abs(_wrap_angle(heading - travel)) > max_off_axis:
        return None
    if max_height is not None and cut.centre[1] > max_height:
        return None
    curvature = _median([_curvature(centres[i - 1], centres[i], centres[i + 1]) for i in range(1, span)])
    return StrokeEnd(
        point=cut.centre,
        heading=heading,
        curvature=curvature,
        width=cut.width,
        nib=fit_nib(skeleton),
    )


def fit_nib(skeleton: Sequence[tuple[Point, float]], *, keep: float = 0.7) -> Nib | None:
    usable = skeleton[: max(int(len(skeleton) * keep), 4)]
    if len(usable) < 4:
        return None
    samples = []
    for i in range(1, len(usable) - 1):
        heading = _heading(usable[i - 1][0], usable[i + 1][0])
        samples.append((heading, usable[i][1]))
    if not samples:
        return None

    best: tuple[float, float, float] | None = None
    for step in range(180):
        angle = math.radians(step)
        across = [abs(math.sin(h - angle)) for h, _ in samples]
        denominator = sum(a * a for a in across)
        if denominator < 1e-9:
            continue
        width = sum(a * w for a, (_, w) in zip(across, samples)) / denominator
        error = sum((w - width * a) ** 2 for a, (_, w) in zip(across, samples))
        if best is None or error < best[0]:
            best = (error, width, angle)
    if best is None or best[1] <= 0:
        return None
    return Nib(best[1], best[2])


def _sample_arc(start: Point, segments: Sequence[tuple[str, tuple[Point, ...]]]) -> list[Point]:
    points = [start]
    current = start
    for kind, args in segments:
        points.extend(sample_segment(current, kind, args, 8)[1:])
        current = args[-1]
    return points


def _resample(points: Sequence[Point], count: int) -> list[Point]:
    if len(points) < 2:
        return []
    steps = [0.0]
    for a, b in zip(points, points[1:]):
        steps.append(steps[-1] + math.dist(a, b))
    total = steps[-1]
    if total <= 0:
        return []
    out = []
    j = 0
    for i in range(count):
        target = total * i / (count - 1)
        while j < len(steps) - 2 and steps[j + 1] < target:
            j += 1
        span = steps[j + 1] - steps[j]
        t = 0.0 if span <= 0 else (target - steps[j]) / span
        out.append(_lerp(points[j], points[j + 1], t))
    return out


def _wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def _heading(a: Point, b: Point) -> float:
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _curvature(p0: Point, p1: Point, p2: Point) -> float:
    ax, ay = p1[0] - p0[0], p1[1] - p0[1]
    bx, by = p2[0] - p1[0], p2[1] - p1[1]
    cross = ax * by - ay * bx
    denominator = math.dist(p0, p1) * math.dist(p1, p2) * math.dist(p0, p2)
    return 0.0 if denominator == 0 else 2.0 * cross / denominator


def _median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _reach_along(path: Path, node: int, step: int, distance: float) -> tuple[int, float] | None:
    count = path.node_count()
    travelled = 0.0
    nodes = path.nodes()
    for taken in range(count - 1):
        index = (node + (taken if step > 0 else -taken - 1)) % len(path.segments)
        kind, points = path.segments[index]
        start = nodes[index % count]
        length = segment_length(start, kind, points)
        if travelled + length >= distance:
            share = (distance - travelled) / length if length else 0.0
            return index, (share if step > 0 else 1.0 - share)
        travelled += length
    return None


def _point_at(path: Path, index: int, t: float) -> Point:
    kind, points = path.segments[index]
    start = path.nodes()[index % path.node_count()]
    return split_segment(start, kind, points, t)[0][1][-1]


def _open_between(
    path: Path, first: tuple[int, float], second: tuple[int, float]
) -> tuple[Path, list[tuple[str, tuple[Point, ...]]]]:
    nodes = path.nodes()
    count = path.node_count()
    (i, ti), (j, tj) = first, second

    def halves(index: int, t: float):
        kind, points = path.segments[index]
        return split_segment(nodes[index % count], kind, points, t)

    before_i, after_i = halves(i, ti)
    before_j, after_j = halves(j, tj)

    kept: list[tuple[str, tuple[Point, ...]]] = [after_j]
    k = (j + 1) % len(path.segments)
    while k != i:
        kept.append(path.segments[k])
        k = (k + 1) % len(path.segments)
    kept.append(before_i)

    removed: list[tuple[str, tuple[Point, ...]]] = [after_i]
    k = (i + 1) % len(path.segments)
    while k != j:
        removed.append(path.segments[k])
        k = (k + 1) % len(path.segments)
    removed.append(before_j)

    start = split_segment(nodes[j % count], *path.segments[j], tj)[0][1][-1]
    return Path(start, kept, closed=False), removed


def body_path(contours: Sequence[Contour]) -> Path | None:
    if not contours:
        return None
    return Path.from_contour(max(contours, key=lambda c: abs(contour_area(c))))
