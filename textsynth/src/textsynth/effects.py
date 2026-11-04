from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol, Sequence

import numpy as np
from scipy import ndimage as ndi

_CONNECTIVITY_8 = np.ones((3, 3), dtype=bool)


class Effect(Protocol):
    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray: ...


@dataclass
class ComponentFilter:
    min_area: int = 1
    max_area: int | None = None
    count: int | None = None
    """The maximum number of components to keep. The filter selects at random."""
    probability: float = 1.0
    """The probability to keep each candidate. Each test is independent."""

    def select(self, areas: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        labels = np.arange(1, len(areas) + 1)
        keep = areas >= self.min_area
        if self.max_area is not None:
            keep &= areas <= self.max_area
        labels = labels[keep]
        if self.probability < 1.0 and len(labels):
            labels = labels[rng.random(len(labels)) < self.probability]
        if self.count is not None and len(labels) > self.count:
            labels = rng.choice(labels, size=self.count, replace=False)
        return labels


@dataclass
class Pipeline:
    effects: Sequence[Effect] = ()

    def __init__(self, *effects: Effect):
        self.effects = list(effects)

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        for effect in self.effects:
            ink = effect.apply(ink, rng)
        return ink


@dataclass
class Smudge:
    length: float = 6.0
    """The length of the smear, in pixels."""
    angle: float = 25.0
    angle_jitter: float = 8.0
    length_jitter: float = 2.0
    strength: float = 0.8
    """The quantity of ink in the smear, in the range ``0`` to ``1``."""
    softness: float = 1.5
    """The Gaussian blur to apply to the smear, in pixels."""
    fade: float = 0.0
    """The quantity of ink to remove from the glyph, in the range ``0`` to ``1``.

    This simulates a pen that becomes dry.
    """
    spread: str = "trail"
    """The direction of the smear.

    The ``"trail"`` value pulls the ink one way. The ``"both"`` value
    spreads the ink the two ways along the axis.
    """
    select: ComponentFilter = field(default_factory=lambda: ComponentFilter(min_area=20, count=5))
    threshold: float = 0.5

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        labels, areas = _components(ink, self.threshold)
        objects = ndi.find_objects(labels)
        out = ink.copy()
        for label in self.select.select(areas, rng):
            angle = self.angle + rng.normal(0.0, self.angle_jitter)
            length = max(1.0, self.length + rng.normal(0.0, self.length_jitter))
            margin = int(length) + int(self.softness * 3) + 2
            box = _grow(objects[int(label) - 1], labels.shape, margin)
            if box is not None:
                out = self._smear(out, labels, int(label), box, angle, length)
        return np.clip(out, 0.0, 1.0)

    def _smear(
        self,
        ink: np.ndarray,
        labels: np.ndarray,
        label: int,
        box: tuple[int, int, int, int],
        angle: float,
        length: float,
    ) -> np.ndarray:
        y0, y1, x0, x1 = box
        mask = (labels[y0:y1, x0:x1] == label).astype(np.float32)

        smear = ndi.convolve(mask, _motion_kernel(length, angle, self.spread), mode="constant")
        if self.softness > 0:
            smear = ndi.gaussian_filter(smear, self.softness)
        peak = float(smear.max())
        if peak <= 0:
            return ink
        smear = smear / peak * self.strength

        region = ink[y0:y1, x0:x1]
        np.maximum(region, smear, out=region)

        if self.fade > 0:
            h, w = mask.shape
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            theta = math.radians(angle)
            ramp = xx * math.cos(theta) - yy * math.sin(theta)
            ramp -= ramp.min()
            ramp /= max(float(ramp.max()), 1e-6)
            region -= self.fade * ramp * mask
            np.clip(region, 0.0, 1.0, out=region)
        return ink


@dataclass
class Blobify:
    merge_radius: float = 4.0
    """The effect joins two marks that are nearer than twice this value, in pixels."""
    fill_radius: float = 2.5
    """The radius of the closing that fills the space between two joined marks."""
    halo: float = 1.0
    """The soft bleed around the joined blob, in pixels."""
    halo_strength: float = 0.35
    probability: float = 0.6
    """The probability that the effect joins a given cluster."""
    keep_single: bool = True
    """Do not change a mark that has no neighbour."""
    select: ComponentFilter = field(default_factory=lambda: ComponentFilter(min_area=2, max_area=120))
    threshold: float = 0.5

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        labels, areas = _components(ink, self.threshold)
        chosen = self.select.select(areas, rng)
        if not len(chosen):
            return ink

        marks = np.isin(labels, chosen)
        groups, group_count = ndi.label(
            ndi.binary_dilation(marks, _disk(self.merge_radius)),
            structure=_CONNECTIVITY_8,
        )
        if group_count == 0:
            return ink

        out = ink.copy()
        closing = _disk(self.fill_radius)
        objects = ndi.find_objects(groups)
        for index, slices in enumerate(objects, start=1):
            if slices is None:
                continue
            group_mask = (groups[slices] == index) & marks[slices]
            if self.keep_single:
                _, n = ndi.label(group_mask, structure=_CONNECTIVITY_8)
                if n < 2:
                    continue
            if rng.random() > self.probability:
                continue

            fused = ndi.binary_closing(group_mask, closing)
            region = out[slices]
            np.maximum(region, fused.astype(np.float32), out=region)

            if self.halo > 0 and self.halo_strength > 0:
                bleed = ndi.gaussian_filter(fused.astype(np.float32), self.halo)
                peak = float(bleed.max())
                if peak > 0:
                    bleed = bleed / peak * self.halo_strength * (~fused)
                    np.maximum(region, bleed, out=region)
        return np.clip(out, 0.0, 1.0)


@dataclass
class Blot:
    distance: float = 2.0
    """The offset of the copy, in pixels."""
    angle: float = -45.0
    """The direction of the offset, in degrees counter-clockwise from +x."""
    thickness: float = 0.0
    """The radius to add to the copy, in pixels."""
    grow: float = 1.0
    """The radius to add to the source mark first. This keeps the blot in one piece."""
    select: ComponentFilter = field(default_factory=lambda: ComponentFilter(min_area=25, count=4))
    threshold: float = 0.5

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        labels, areas = _components(ink, self.threshold)
        chosen = self.select.select(areas, rng)
        if not len(chosen):
            return ink

        theta = math.radians(self.angle)
        dx = int(round(self.distance * math.cos(theta)))
        dy = int(round(-self.distance * math.sin(theta)))

        patch = np.isin(labels, chosen)
        if self.grow >= 1:
            patch = ndi.binary_dilation(patch, _disk(self.grow))
        patch = ndi.shift(patch, (dy, dx), order=0, mode="constant", cval=False)
        if self.thickness >= 1:
            patch = ndi.binary_dilation(patch, _disk(self.thickness))
        return np.maximum(ink, patch.astype(np.float32))


@dataclass
class InkBleed:
    radius: float = 1.0
    strength: float = 1.0
    softness: float = 0.6

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        grown = ndi.grey_dilation(ink, footprint=_disk(self.radius))
        if self.softness > 0:
            grown = ndi.gaussian_filter(grown, self.softness)
        return np.clip(ink + (grown - ink) * self.strength, 0.0, 1.0)


@dataclass
class Erode:
    radius: float = 1.0
    strength: float = 1.0

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        thinned = ndi.grey_erosion(ink, footprint=_disk(self.radius))
        return np.clip(ink - (ink - thinned) * self.strength, 0.0, 1.0)


@dataclass
class Blur:
    sigma: float = 1.0

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        return np.clip(ndi.gaussian_filter(ink, self.sigma), 0.0, 1.0)


@dataclass
class Speckle:
    density: float = 0.002
    """The fraction of the pixels that become specks."""
    size: float = 0.8
    """The radius of a speck, in pixels."""
    strength: float = 0.7
    holes: float = 0.0
    """The fraction of the pixels in the ink that become pinholes."""

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        out = ink
        if self.density > 0:
            seeds = (rng.random(ink.shape) < self.density).astype(np.float32)
            specks = ndi.gaussian_filter(seeds, self.size)
            peak = float(specks.max())
            if peak > 0:
                out = np.maximum(out, specks / peak * self.strength)
        if self.holes > 0:
            seeds = (rng.random(ink.shape) < self.holes).astype(np.float32)
            holes = ndi.gaussian_filter(seeds, self.size)
            peak = float(holes.max())
            if peak > 0:
                out = out * (1.0 - np.clip(holes / peak, 0.0, 1.0))
        return np.clip(out, 0.0, 1.0)


@dataclass
class Threshold:
    level: float = 0.5
    softness: float = 0.05

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        if self.softness <= 0:
            return (ink >= self.level).astype(np.float32)
        return np.clip((ink - self.level) / self.softness + 0.5, 0.0, 1.0)


@dataclass
class Warp:
    amplitude: float = 2.0
    """The offset, in pixels."""
    scale: float = 24.0
    """The correlation length of the offset field, in pixels."""

    def apply(self, ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        h, w = ink.shape
        dy, dx = (ndi.gaussian_filter(rng.normal(0.0, 1.0, (h, w)), self.scale) for _ in range(2))
        for field_ in (dy, dx):
            peak = float(np.abs(field_).max())
            if peak > 0:
                field_ *= self.amplitude / peak
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        return np.clip(
            ndi.map_coordinates(ink, [yy + dy, xx + dx], order=1, mode="constant"),
            0.0,
            1.0,
        )


def _components(ink: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    labels, count = ndi.label(ink >= threshold, structure=_CONNECTIVITY_8)
    if count == 0:
        return labels, np.zeros(0, dtype=np.int64)
    areas = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    return labels, areas


def _grow(slices: tuple[slice, slice] | None, shape: tuple[int, int], margin: int) -> tuple[int, int, int, int] | None:
    if slices is None:
        return None
    ys, xs = slices
    h, w = shape
    return (
        max(0, ys.start - margin),
        min(h, ys.stop + margin),
        max(0, xs.start - margin),
        min(w, xs.stop + margin),
    )


def _disk(radius: float) -> np.ndarray:
    r = max(0.5, float(radius))
    size = int(2 * math.ceil(r) + 1)
    c = size // 2
    yy, xx = np.mgrid[0:size, 0:size]
    return ((yy - c) ** 2 + (xx - c) ** 2) <= r * r


def _motion_kernel(length: float, angle_deg: float, spread: str = "trail") -> np.ndarray:
    length = max(1.0, float(length))
    size = int(2 * math.ceil(length) + 1)
    kernel = np.zeros((size, size), dtype=np.float32)
    c = size // 2
    theta = math.radians(angle_deg)
    dx, dy = math.cos(theta), -math.sin(theta)
    start = -length / 2.0 if spread == "both" else 0.0
    for t in np.linspace(start, start + length, max(2, int(length * 4))):
        x, y = c + dx * t, c + dy * t
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - x0, y - y0
        for yi, wy in ((y0, 1 - fy), (y0 + 1, fy)):
            for xi, wx in ((x0, 1 - fx), (x0 + 1, fx)):
                if 0 <= yi < size and 0 <= xi < size:
                    kernel[yi, xi] += wy * wx
    total = kernel.sum()
    return kernel / total if total else kernel
