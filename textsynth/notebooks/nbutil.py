from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT = ASSETS / "fonts" / "Amiri-Regular.ttf"
DONOR = ASSETS / "fonts" / "Oblegg-Jawi.otf"

PLAIN = ASSETS / "fonts" / "ScheherazadeNew-Regular.ttf"


def label_font(size: int = 15, arabic: bool = False) -> ImageFont.ImageFont:
    if arabic:
        return ImageFont.truetype(str(FONT), size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def sheet(
    rows: list[tuple[str, Image.Image]],
    gutter: int = 180,
    font: ImageFont.ImageFont | None = None,
) -> Image.Image:
    font = font or label_font()
    width = gutter + max(image.width for _, image in rows)
    canvas = Image.new("L", (width, sum(i.height for _, i in rows)), 255)
    draw = ImageDraw.Draw(canvas)
    y = 0
    for text, image in rows:
        canvas.paste(image, (width - image.width, y))
        draw.text((12, y + image.height // 2 - 8), text, fill=90, font=font)
        y += image.height
    return canvas


def columns(
    rows: list[tuple[str, ...]],
    headings: tuple[str, ...] = (),
    gutter: int = 90,
    font: ImageFont.ImageFont | None = None,
) -> Image.Image:
    heading_font = label_font()
    font = font or heading_font
    images = [[cell for cell in row[1:]] for row in rows]
    width = max(max(i.width for i in cells) for cells in images) + 20
    top = 22 if headings else 0
    height = top + sum(max(i.height for i in cells) for cells in images)
    canvas = Image.new("L", (gutter + width * len(images[0]), height), 255)
    draw = ImageDraw.Draw(canvas)
    for i, heading in enumerate(headings):
        draw.text((gutter + width * i + 10, 4), heading, fill=140, font=heading_font)
    y = top
    for row, cells in zip(rows, images):
        for i, image in enumerate(cells):
            canvas.paste(image, (gutter + width * (i + 1) - image.width, y))
        tall = max(i.height for i in cells)
        draw.text((12, y + tall // 2 - 8), row[0], fill=90, font=font)
        y += tall
    return canvas
