from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Layout:
    size: float = 64.0
    """The em size in pixels."""

    tracking: float = 0.0
    """The pixels to add to each glyph advance. The value can be negative."""

    word_spacing: float = 0.0
    """The pixels to add to each space advance, additional to ``tracking``."""

    line_spacing: float = 1.35
    """The distance from baseline to baseline, as a multiple of ``size``."""

    padding: int | tuple[int, int] | tuple[int, int, int, int] = 40
    """The margin around the inked area: ``all``, ``(x, y)``, or ``(l, t, r, b)``."""

    align: str = "auto"
    """One of ``"auto"``, ``"left"``, ``"right"``, or ``"center"``.

    The ``"auto"`` value aligns to the right for right-to-left text.
    """

    jitter_x: float = 0.0
    """The standard deviation, in pixels, of the random horizontal offset."""

    jitter_y: float = 0.0
    """The standard deviation, in pixels, of the random vertical offset."""

    jitter_rotation: float = 0.0
    """The standard deviation, in degrees, of the random glyph rotation."""

    supersample: int = 1
    """Render at N times the size, then downsample.

    This makes the edges smoother, but it also makes the render slower.
    """

    def padding_box(self) -> tuple[int, int, int, int]:
        p = self.padding
        if isinstance(p, (int, float)):
            v = int(p)
            return v, v, v, v
        if len(p) == 2:
            x, y = p
            return int(x), int(y), int(x), int(y)
        if len(p) == 4:
            return tuple(int(v) for v in p)
        raise ValueError(f"padding must be a number, a 2-tuple or a 4-tuple; got {p!r}")
