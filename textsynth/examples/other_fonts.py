from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from textsynth import (
    Blobify,
    BorrowedGlyph,
    Font,
    GlyphSubstitution,
    InkBleed,
    Kashida,
    KashidaForms,
    Layout,
    Synthesizer,
    Smudge,
    Speckle,
    SweepShape,
    TadakhulMerged,
    orthographic_variation,
)
from textsynth.patching import patch_font
from textsynth.shaping import shape
from textsynth.sweeps import SweptGlyph, free_after

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
AMIRI = ROOT / "assets" / "fonts" / "Amiri-Regular.ttf"
DONOR = ROOT / "assets" / "fonts" / "Oblegg-Jawi.otf"

SYSTEM = Path("/System/Library/Fonts")
SUPPLEMENTAL = SYSTEM / "Supplemental"

LINE = "بسم الله الرحمن الرحيم"
JAWI = "ڠاجرن ساي دڠن ڤنوه"
ALPHABET = "ابتثجحخدذرزسشصضطظعغفقكلمنهوىءةپچژگکیڤڠڽݢۏھڭؤڑۆے"

ORTHOGRAPHIES = {
    "Arabic": "ابتثجحخدذرزسشصضطظعغفقكلمنهوىءةأإآؤئ",
    "Persian": "پچژگک",
    "Urdu": "ٹڈڑںھے",
    "Jawi": "ڠڽݢۏڤچ",
    "Pashto": "ټډړږځڅڼ",
    "Sorani": "ڵڕۆێ",
    "marks": "ًٌٍَُِّْٰ",
}


@dataclass
class Face:
    label: str
    path: Path
    index: int = 0
    style: str = "naskh"
    tech: str = "GSUB"
    sweep: tuple[str, str, str] = ("و", "والله", "waw")


PANEL = [
    Face("Amiri", AMIRI),
    Face("SF Arabic", SYSTEM / "SFArabic.ttf", style="sans"),
    Face(
        "Noto Nastaliq Urdu",
        SYSTEM / "NotoNastaliq.ttc",
        style="nastaliq",
        sweep=("پ", "پاک", "peh"),
    ),
    Face("Damascus", SUPPLEMENTAL / "Damascus.ttc", tech="GSUB+AAT"),
    Face("Geeza Pro", SYSTEM / "GeezaPro.ttc", tech="AAT"),
    Face("DecoType Naskh", SUPPLEMENTAL / "DecoTypeNaskh.ttc", tech="AAT"),
    Face(
        "Diwan Kufi",
        SUPPLEMENTAL / "Diwan Kufi.ttc",
        style="kufi",
        tech="AAT",
        sweep=("س", "سلام", "seen"),
    ),
    Face("Nadeem", SUPPLEMENTAL / "Nadeem.ttc", tech="AAT"),
    Face("Mishafi", SUPPLEMENTAL / "Mishafi.ttf", tech="AAT", sweep=("س", "سلام", "seen")),
]


def label_font(size: int = 14) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def sheet(rows: list[tuple[str, list[Image.Image]]], *, gutter: int = 200, title: str = "") -> Image.Image:
    font = label_font()
    columns = max(len(images) for _, images in rows)
    width = max(max(image.width for image in images) for _, images in rows) + 16
    top = 26 if title else 0
    canvas = Image.new(
        "L",
        (gutter + width * columns, top + sum(max(i.height for i in images) for _, images in rows)),
        255,
    )
    draw = ImageDraw.Draw(canvas)
    if title:
        draw.text((12, 6), title, fill=0, font=label_font(16))
    y = top
    for text, images in rows:
        height = max(image.height for image in images)
        for column, image in enumerate(images):
            canvas.paste(image, (gutter + width * (column + 1) - image.width - 8, y + (height - image.height) // 2))
        lines = text.split("\n")
        for i, line in enumerate(lines):
            draw.text((12, y + height // 2 - 8 + (i - (len(lines) - 1) / 2) * 15), line, fill=70, font=font)
        draw.line((0, y, canvas.width, y), fill=220)
        y += height
    return canvas


def load_panel(extra: list[str]) -> list[tuple[Face, Font]]:
    faces = PANEL + [Face(Path(p).stem, Path(p), style="?", tech="?") for p in extra]
    panel = []
    for face in faces:
        if not face.path.exists():
            print(f"  skipped {face.label}: not on this machine")
            continue
        panel.append((face, Font(face.path, face.index)))
    return panel


def sweepers(font: Font) -> str:
    found = []
    for letter in dict.fromkeys(ALPHABET):
        if not font.covers(letter):
            continue
        text = "سم" + letter + ("ادب" if free_after("سم" + letter + "ا", 2) else " ادب")
        try:
            glyphs = [g for g in shape(text, font) if g.cluster == 2]
            end = (
                SweptGlyph(font=font, glyph=glyphs[0].name, shape=SweepShape()).end
                if glyphs and free_after(text, 2)
                else None
            )
        except Exception:
            end = None
        if end is not None:
            found.append(letter)
    return "".join(found)


def patch_reaches_shaper(font: Font) -> bool:
    before = [g.name for g in shape("ممتاز", font)]
    patched = patch_font(font, [GlyphSubstitution("مم", BorrowedGlyph(DONOR, "A"))])
    return [g.name for g in shape("ممتاز", patched)] != before


def ink_height(font: Font, size: int = 64) -> int:
    image = np.asarray(Synthesizer(font=font, layout=Layout(size=size, padding=0))(LINE))
    rows = np.where((image < 200).any(axis=1))[0]
    return int(rows.max() - rows.min() + 1) if len(rows) else 0


def report(panel: list[tuple[Face, Font]]) -> None:
    header = f"{'font':22} {'tech':9} {'GSUB patch':11} {'ink @64':8} coverage / sweeps from"
    print(header)
    print("-" * len(header))
    for face, font in panel:
        missing = [
            f"{name} {sum(font.covers(c) for c in letters)}/{len(letters)}"
            for name, letters in ORTHOGRAPHIES.items()
            if not all(font.covers(c) for c in letters)
        ]
        print(
            f"{face.label:22} {face.tech:9} {str(patch_reaches_shaper(font)):11} "
            f"{ink_height(font):>5} px  {', '.join(missing) or 'all orthographies'}"
        )
        print(f"{'':22} sweeps from: {sweepers(font) or '(no letter has a free terminal)'}")


def plain(panel) -> Image.Image:
    layout = Layout(size=56, padding=(20, 12), supersample=2)
    return sheet(
        [
            (f"{face.label}\n{face.style} · {face.tech}", [Synthesizer(font=font, layout=layout)(LINE)])
            for face, font in panel
        ],
        title="the same line in each face: shaping and layout only",
    )


def kashida(panel) -> Image.Image:
    layout = Layout(size=64, padding=(20, 12), supersample=2)
    rows = []
    for face, font in panel:
        rules = [Kashida(frequency=5)]
        rows.append((
            f"{face.label}\n{face.tech}",
            [
                Synthesizer(font=font, layout=layout, text_rules=rules, seed=1)("حكيم مبين"),
                Synthesizer(
                    font=font,
                    layout=layout,
                    text_rules=rules,
                    font_patches=[KashidaForms()],
                    seed=1,
                )("حكيم مبين"),
            ],
        ))
    return sheet(rows, title="kashida: tatweels only (left) · with KashidaForms (right)")


def sweep(panel) -> Image.Image:
    layout = Layout(size=110, padding=(24, 16), supersample=2)
    rows = []
    for face, font in panel:
        letter, word, letter_name = face.sweep
        rule = TadakhulMerged(letters=letter, length=3)
        rows.append((
            f"{face.label}\n{face.style} · from {letter_name}",
            [
                Synthesizer(font=font, layout=layout)(word),
                Synthesizer(font=font, layout=layout, glyph_rules=[rule])(word),
            ],
        ))
    return sheet(rows, title="tadakhul: plain (left) · swept (right)")


def substitution(panel) -> Image.Image:
    layout = Layout(size=64, padding=(20, 12), supersample=2)
    rows = []
    for face, font in panel:
        patch = GlyphSubstitution("مم", BorrowedGlyph(DONOR, "A"))
        rows.append((
            f"{face.label}\n{face.tech}",
            [
                Synthesizer(font=font, layout=layout)("ممتاز"),
                Synthesizer(font=font, layout=layout, font_patches=[patch])("ممتاز"),
            ],
        ))
    return sheet(rows, title="the pair mim-mim drawn by a borrowed glyph: before (left) · after (right)")


def fallback(panel) -> Image.Image:
    layout = Layout(size=56, padding=(20, 12), supersample=2)
    rows = []
    for face, font in panel:
        if all(font.covers(c) for c in "ڠڤ"):
            continue
        rows.append((
            f"{face.label}\nno nga",
            [
                Synthesizer(font=font, layout=layout)(JAWI),
                Synthesizer(font=font, layout=layout, fallbacks=[AMIRI])(JAWI),
            ],
        ))
    return sheet(rows, title="Jawi in a face that lacks it: alone (left) · with an Amiri fallback (right)")


def mixed(panel) -> Image.Image:
    faces = dict((face.label, font) for face, font in panel)
    recipes = [
        (
            "kashida + smudge",
            dict(
                text_rules=[Kashida(frequency=6, contrast=0.8)],
                font_patches=[KashidaForms()],
                effects=[Smudge(length=7)],
            ),
            LINE,
        ),
        (
            "sweep + ink bleed",
            dict(glyph_rules=[TadakhulMerged(letters="و", length=3)], effects=[InkBleed(1.2)]),
            "وروده الى المدينة",
        ),
        (
            "tight + varied\nspelling + blobs",
            dict(text_rules=[orthographic_variation(swap=0.35)], effects=[Blobify(), InkBleed(0.8)]),
            LINE,
        ),
        (
            "sweep + speckle",
            dict(glyph_rules=[TadakhulMerged(letters="و", length=2)], effects=[Speckle(density=0.004)]),
            "والله نور",
        ),
        ("kashida, tatweels only", dict(text_rules=[Kashida(frequency=4)], effects=[InkBleed(0.6)]), LINE),
        ("plain, jittered", dict(effects=[Smudge(length=4, strength=0.5)]), LINE),
    ]
    layout = Layout(size=58, padding=(22, 14), supersample=2, jitter_y=0.6, tracking=-0.5)
    rows = []
    for (label, kwargs, text), (name, font) in zip(recipes, faces.items()):
        rows.append((
            f"{name}\n{label}",
            [Synthesizer(font=font, layout=layout, seed=11, **kwargs)(text)],
        ))
    return sheet(rows, gutter=220, title="a mixed page: one face and one recipe for each line")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    panel = load_panel(sys.argv[1:])
    report(panel)
    for name, build in (
        ("plain", plain),
        ("kashida", kashida),
        ("sweep", sweep),
        ("substitution", substitution),
        ("fallback", fallback),
        ("mixed", mixed),
    ):
        start = time.perf_counter()
        path = OUT / f"fonts-{name}.png"
        build(panel).save(path)
        print(f"wrote {path.relative_to(ROOT)} ({time.perf_counter() - start:.1f} s)")


if __name__ == "__main__":
    main()
