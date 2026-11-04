from __future__ import annotations

import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from textsynth import (
    REVERSE_SWEEPERS,
    Font,
    Layout,
    Synthesizer,
    SweepShape,
    TadakhulMerged,
    TadakhulQuantised,
    TadakhulScaled,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FONT = ROOT / "assets" / "fonts" / "Amiri-Regular.ttf"

TEXT = "والله"
LONGER = "وروده الى المدينة"

NG = "سمبهيڠ"

KAMPUNG = "كامڤوڠ"

AIN = "جامع"


def label_font(size: int = 15) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def sheet(rows: list[tuple[str, Image.Image]], gutter: int = 190) -> Image.Image:
    font = label_font()
    width = gutter + max(image.width for _, image in rows)
    height = sum(image.height for _, image in rows)
    canvas = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(canvas)
    y = 0
    for text, image in rows:
        canvas.paste(image, (width - image.width, y))
        draw.text((12, y + image.height // 2 - 8), text, fill=90, font=font)
        y += image.height
    return canvas


def columns(
    rows: list[tuple[str, Image.Image, Image.Image]],
    headings: tuple[str, str] = (),
    gutter: int = 190,
) -> Image.Image:
    font = label_font()
    width = max(max(a.width, b.width) for _, a, b in rows) + 20
    top = 22 if headings else 0
    height = top + sum(max(a.height, b.height) for _, a, b in rows)
    canvas = Image.new("L", (gutter + width * 2, height), 255)
    draw = ImageDraw.Draw(canvas)
    for i, heading in enumerate(headings):
        draw.text((gutter + width * i + 10, 4), heading, fill=140, font=font)
    y = top
    for label, left, right in rows:
        tall = max(left.height, right.height)
        draw.text((12, y + tall // 2 - 8), label, fill=90, font=font)
        canvas.paste(left, (gutter + width - left.width, y))
        canvas.paste(right, (gutter + width * 2 - right.width, y))
        y += tall
    return canvas


def timed(synth: Synthesizer, text: str) -> tuple[Image.Image, float, float]:
    start = time.perf_counter()
    synth.patched_font
    build = time.perf_counter() - start
    start = time.perf_counter()
    image = synth(text)
    return image, build, time.perf_counter() - start


def options() -> Image.Image:
    layout = Layout(size=130, padding=22, supersample=2)
    rows = [("no sweep", Synthesizer(font=FONT, layout=layout)(TEXT))]
    for name, rule in (
        ("merged\nexact, rebuilds", TadakhulMerged(letters="و", length=4)),
        ("quantised\nladder of 8", TadakhulQuantised(letters="و", length=4)),
        ("scaled\none stroke, stretched", TadakhulScaled(letters="و", length=4)),
    ):
        synth = Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])
        image, build, draw = timed(synth, TEXT)
        rows.append((f"{name}\nbuild {build * 1000:.0f} ms · draw {draw * 1000:.0f} ms", image))
    return sheet(rows, gutter=230)


def lengths() -> Image.Image:
    layout = Layout(size=110, padding=18, supersample=2)
    rows = []
    for length in range(1, 5):
        rule = TadakhulMerged(letters="و", length=length)
        rows.append((f"length = {length}", Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(TEXT)))
    return sheet(rows, gutter=120)


def several() -> Image.Image:
    layout = Layout(size=110, padding=18, supersample=2)
    rows = []
    for text, length in (("واوا", 1), ("واوا", 2), (LONGER, 2), (LONGER, 4)):
        rule = TadakhulMerged(letters="و", length=length)
        rows.append((
            f"{length} letter(s) each",
            Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(text),
        ))
    return sheet(rows, gutter=140)


def reverse() -> Image.Image:
    layout = Layout(size=110, padding=18, supersample=2)
    rows = [("no sweep", Synthesizer(font=FONT, layout=layout)(NG))]
    for length in range(1, 5):
        rule = TadakhulMerged(letters="", reverse_letters=REVERSE_SWEEPERS, length=length)
        rows.append((
            f"ng, length = {length}",
            Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(NG),
        ))
    for text, name in ((AIN, "ain"), (KAMPUNG, "ng")):
        rule = TadakhulMerged(letters="", reverse_letters=REVERSE_SWEEPERS, length=3)
        rows.append(("no sweep", Synthesizer(font=FONT, layout=layout)(text)))
        rows.append((
            f"{name}, length = 3",
            Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(text),
        ))
    return sheet(rows, gutter=140)


def directions() -> Image.Image:
    layout = Layout(size=110, padding=18, supersample=2)
    rows = []
    for label, text, rule in (
        ("waw sweeps left\nbelow the letters after", TEXT, TadakhulMerged(letters="و", length=3)),
        (
            "ng sweeps right\nbelow the letters before",
            NG,
            TadakhulMerged(letters="", reverse_letters=REVERSE_SWEEPERS, length=3),
        ),
        (
            "ain sweeps right\nbelow the letters before",
            AIN,
            TadakhulMerged(letters="", reverse_letters=REVERSE_SWEEPERS, length=3),
        ),
    ):
        rows.append((
            label,
            Synthesizer(font=FONT, layout=layout)(text),
            Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(text),
        ))
    return columns(rows, headings=("plain", "swept"), gutter=210)


ALPHABET = "ابتثجحخدذرزسشصضطظعغفقكلمنهوىءةپچژگکیڤڠڽݢۏھڭؤڑۆے"


def _probe_text(letter: str, direction: int) -> tuple[str, int]:
    from textsynth.sweeps import free_after

    if direction < 0:
        tail = "ادب" if free_after("سم" + letter + "ا", 2) else " ادب"
        return "سم" + letter + tail, 2
    return "سمبه" + letter, 4


def letters() -> Image.Image:
    from textsynth import Font
    from textsynth.shaping import shape
    from textsynth.sweeps import SweptGlyph, free_after

    font = Font(FONT)
    layout = Layout(size=95, padding=14, supersample=2)
    rows, refused = [], []
    for letter in dict.fromkeys(ALPHABET):
        if not font.covers(letter):
            continue
        found = False
        for direction, word in ((-1, "left"), (1, "right")):
            text, at = _probe_text(letter, direction)
            if not free_after(text, at):
                continue
            glyphs = [g for g in shape(text, font) if g.cluster == at]
            if not glyphs:
                continue
            end = SweptGlyph(
                font=font,
                glyph=glyphs[0].name,
                shape=SweepShape(),
                direction=direction,
            ).end
            if end is None:
                continue
            found = True
            rule = (
                TadakhulMerged(letters=letter, length=3)
                if direction < 0
                else TadakhulMerged(letters="", reverse_letters=letter, length=3)
            )
            rows.append((
                letter,
                word,
                Synthesizer(font=FONT, layout=layout)(text),
                Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(text),
            ))
        if not found:
            refused.append(letter)

    left = [letter for letter, word, _, _ in rows if word == "left"]
    right = [letter for letter, word, _, _ in rows if word == "right"]
    print(f"  sweeps to the left: {' '.join(left)}")
    print(f"  sweeps to the right: {' '.join(right)}")
    print(f"  no terminal to sweep from: {' '.join(refused)}")

    font_label = ImageFont.truetype(str(FONT), 30)
    font_word = label_font()
    column = max(max(a.width, b.width) for _, _, a, b in rows) + 20
    canvas = Image.new(
        "L",
        (86 + column * 2, sum(max(a.height, b.height) for _, _, a, b in rows)),
        255,
    )
    draw = ImageDraw.Draw(canvas)
    y = 0
    for letter, word, plain, swept in rows:
        height = max(plain.height, swept.height)
        draw.text((16, y + height // 2 - 18), letter, fill=90, font=font_label)
        draw.text((16, y + height // 2 + 14), word, fill=140, font=font_word)
        canvas.paste(plain, (86 + column - plain.width, y))
        canvas.paste(swept, (86 + column * 2 - swept.width, y))
        y += height
    return canvas


def shapes() -> Image.Image:
    layout = Layout(size=120, padding=20, supersample=2)
    rows = []
    for name, shape in (
        ("default", SweepShape()),
        ("bottoms out sooner\n(belly 0.55)", SweepShape(belly=0.55)),
        ("bottoms out later\n(belly 0.85)", SweepShape(belly=0.85)),
        ("holds the letter's curve\nlonger (ease 0.08)", SweepShape(ease=0.08)),
        ("nib fitted to the letter\ninstead of 135 degrees", SweepShape(nib_angle=None)),
        ("nib at 115 degrees", SweepShape(nib_angle=115)),
        ("cut back further\n(0.34 em)", SweepShape(cut_back=0.34)),
    ):
        rule = TadakhulMerged(letters="و", length=4, shape=shape)
        rows.append((name, Synthesizer(font=FONT, layout=layout, glyph_rules=[rule])(TEXT)))
    return sheet(rows, gutter=220)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    Font(FONT)
    for name, build in (
        ("options", options),
        ("lengths", lengths),
        ("several", several),
        ("letters", letters),
        ("shapes", shapes),
        ("reverse", reverse),
        ("directions", directions),
    ):
        path = OUT / f"tadakhul-{name}.png"
        build().save(path)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
