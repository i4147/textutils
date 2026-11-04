from __future__ import annotations

from pathlib import Path

import numpy as np

from textsynth import (
    Blobify,
    BorrowedGlyph,
    ComponentFilter,
    GlyphSubstitution,
    InkBleed,
    Kashida,
    KashidaForms,
    Layout,
    Smudge,
    Speckle,
    Synthesizer,
    TadakhulMerged,
    orthographic_variation,
)
from textsynth.kashida import JOINS_FORWARD

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ROOT / "out"

FONT = ASSETS / "fonts" / "Amiri-Regular.ttf"
DONOR = ASSETS / "fonts" / "Oblegg-Jawi.otf"

PLAIN = ASSETS / "fonts" / "ScheherazadeNew-Regular.ttf"

TEXT = "سايا ممباچ سورت خبر"

LAYOUT = Layout(size=96, tracking=-1, padding=24, supersample=2)

MIM = GlyphSubstitution("مم", BorrowedGlyph(DONOR, "A"))

FORMS = KashidaForms(letters="بتثنيسشمكچ", max_run=5, dot_shift=0.5)

SWEEP = TadakhulMerged(letters="و", length=3)

KASHIDA = Kashida(
    frequency=5,
    contrast=0.7,
    min_length=4,
    joins_forward=JOINS_FORWARD.replace("م", ""),
)

INK = [
    Smudge(length=6, strength=0.7, select=ComponentFilter(min_area=20, count=5)),
    Blobify(merge_radius=4, probability=0.7),
    InkBleed(1.0, strength=0.55),
    Speckle(density=0.0012, holes=0.008),
]


def stack(images, gap=18, background=255):
    from PIL import Image

    width = max(i.width for i in images)
    height = sum(i.height for i in images) + gap * (len(images) - 1)
    sheet = Image.new("L", (width, height), background)
    y = 0
    for image in images:
        sheet.paste(image, (width - image.width, y))
        y += image.height + gap
    return sheet


def before_and_after() -> None:
    from PIL import Image, ImageDraw, ImageFont

    try:
        label_font = ImageFont.load_default(size=22)
    except TypeError:
        label_font = ImageFont.load_default()

    before = Synthesizer(font=PLAIN, layout=LAYOUT)(TEXT)
    after = Synthesizer(
        font=PLAIN,
        layout=Layout(size=96, tracking=-1, padding=24, supersample=2, jitter_y=0.5),
        text_rules=[orthographic_variation(swap=0.25), KASHIDA],
        font_patches=[MIM, FORMS],
        glyph_rules=[SWEEP],
        effects=INK,
        seed=3,
    )(TEXT)

    gutter, margin = 26, 8
    width = max(before.width, after.width)
    height = before.height + after.height + gutter + margin * 2
    sheet = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(sheet)

    sheet.paste(before, (width - before.width, margin))
    draw.text((10, margin + 4), "before", font=label_font, fill=110)
    y = margin + before.height + gutter
    sheet.paste(after, (width - after.width, y))
    draw.text((10, y + 4), "after", font=label_font, fill=110)
    draw.line((0, y - gutter // 2, width, y - gutter // 2), fill=205)

    sheet.save(OUT / "all-tricks-before-after.png")
    print(f"all-tricks-before-after.png  {sheet.size}")
    print(f"  before: Scheherazade New, no rules   {before.size}")
    print(f"  after:  every feature                {after.size}")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    everything = Synthesizer(
        font=FONT,
        layout=Layout(size=96, tracking=-1, padding=24, supersample=2, jitter_y=0.5),
        text_rules=[
            orthographic_variation(swap=0.25),
            KASHIDA,
        ],
        font_patches=[MIM, FORMS],
        glyph_rules=[SWEEP],
        effects=INK,
        seed=3,
    )
    image = everything(TEXT)
    image.save(OUT / "all-tricks.png")
    drawn = everything.apply_text_rules(TEXT, np.random.default_rng(3))
    print(f"all-tricks.png  {image.size}")
    print(f"  drawn: {drawn}")
    print(f"  mim-mim pair survived the spelling variation: {'مم' in drawn}")

    rows = [
        ("plain", {}),
        ("+ mim-mim glyph", {"font_patches": [MIM]}),
        (
            "+ kashida, dots carried",
            {
                "font_patches": [MIM, FORMS],
                "text_rules": [KASHIDA],
            },
        ),
        (
            "+ tadakhul on the waw",
            {
                "font_patches": [MIM, FORMS],
                "text_rules": [KASHIDA],
                "glyph_rules": [SWEEP],
            },
        ),
        (
            "+ ink",
            {
                "font_patches": [MIM, FORMS],
                "text_rules": [KASHIDA],
                "glyph_rules": [SWEEP],
                "effects": INK,
            },
        ),
    ]
    images = []
    for label, kwargs in rows:
        synth = Synthesizer(font=FONT, layout=LAYOUT, seed=3, **kwargs)
        rendered = synth(TEXT)
        images.append(rendered)
        print(f"  {label:24} {rendered.size}")
    stack(images).save(OUT / "all-tricks-buildup.png")
    print("all-tricks-buildup.png")

    for i in range(4):
        everything.render(TEXT, seed=i).save(OUT / f"all-tricks-dataset-{i}.png")
        spelling = everything.apply_text_rules(TEXT, np.random.default_rng(i))
        print(f"  dataset {i}: {spelling}")

    before_and_after()

    print(f"wrote images to {OUT}")


if __name__ == "__main__":
    main()
