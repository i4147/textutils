from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from textsynth import Kashida, KashidaForms, Layout, Synthesizer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FONT = ROOT / "assets" / "fonts" / "Amiri-Regular.ttf"

LINE = "بسم الله الرحمن الرحيم"


def label_font(size: int = 15) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def pairs(rows: list[tuple[str, Image.Image, Image.Image]], gutter: int = 120) -> Image.Image:
    font = label_font()
    column = max(max(a.width, b.width) for _, a, b in rows) + 24
    height = sum(max(a.height, b.height) for _, a, b in rows)
    canvas = Image.new("L", (gutter + column * 2, height), 255)
    draw = ImageDraw.Draw(canvas)
    y = 0
    for text, plain, patched in rows:
        draw.text((12, y + max(plain.height, patched.height) // 2 - 8), text, fill=90, font=font)
        canvas.paste(plain, (gutter + column - plain.width, y))
        canvas.paste(patched, (gutter + column * 2 - patched.width, y))
        y += max(plain.height, patched.height)
    draw.text((gutter + column - 130, 4), "tatweel only", fill=140, font=font)
    draw.text((gutter + column * 2 - 130, 4), "dots adapted", fill=140, font=font)
    return canvas


def compare(texts: list[str], letters: str, size: int = 100) -> Image.Image:
    layout = Layout(size=size, padding=16, supersample=2)
    plain = Synthesizer(font=FONT, layout=layout)
    patched = Synthesizer(font=FONT, layout=layout, font_patches=[KashidaForms(letters=letters, max_run=5)])
    return pairs([(text, plain(text), patched(text)) for text in texts])


def contrast() -> Image.Image:
    layout = Layout(size=64, padding=16, supersample=2)
    patch = KashidaForms(letters="بتثنيشسجفقغعصضطظكم", max_run=6)
    rows = []
    font = label_font()
    for value in (0.0, 0.4, 0.8, 1.0):
        synth = Synthesizer(
            font=FONT,
            layout=layout,
            text_rules=[Kashida(frequency=6, contrast=value)],
            font_patches=[patch],
        )
        rows.append((f"contrast {value}", synth(LINE)))
    width = 120 + max(image.width for _, image in rows)
    canvas = Image.new("L", (width, sum(image.height for _, image in rows)), 255)
    draw = ImageDraw.Draw(canvas)
    y = 0
    for text, image in rows:
        canvas.paste(image, (width - image.width, y))
        draw.text((12, y + image.height // 2 - 8), text, fill=90, font=font)
        y += image.height
    return canvas


def main() -> None:
    OUT.mkdir(exist_ok=True)
    compare(["ب" + "ـ" * n + "سم" for n in range(5)], letters="ب").save(OUT / "kashida-dots.png")
    compare(
        ["بــــسم", "نــــا", "ثــــم", "شــــم", "يــــا", "فــــي", "قــــا", "جــــا"],
        letters="بتثنيشسجفق",
        size=84,
    ).save(OUT / "kashida-letters.png")
    contrast().save(OUT / "kashida-contrast.png")

    elongated = Kashida(frequency=6, contrast=0.8).apply(LINE, np.random.default_rng(0))
    print("kashida-js port, contrast 0.8:", elongated)
    for name in ("dots", "letters", "contrast"):
        print(f"wrote out/kashida-{name}.png")


if __name__ == "__main__":
    main()
