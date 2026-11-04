from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from ..generators import register_generator


def get_text_dimensions(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def get_system_font(size: int = 24) -> ImageFont.FreeTypeFont:
    try:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except IOError:
            try:
                return ImageFont.truetype("Arial.ttf", size)
            except IOError:
                return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def create_text_image(
    content: str,
    width: int = 800,
    height: int = 400,
    bg_color: str = "#f0f0f0",
    text_color: str = "#333333",
    font_size: int = 24,
    padding: int = 40,
) -> Image.Image:
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    try:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), content, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), content, fill=text_color, font=font)
    return image


@register_generator(["jpg", "jpeg", "png", "bmp", "gif"])
def generate_image_file(content: str, output_path: Path) -> Path:
    try:
        image = create_text_image(
            content=content,
            width=800,
            height=400,
            bg_color="#f8f9fa",
            text_color="#2c3e50",
            font_size=36,
            padding=40,
        )

        image_format = output_path.suffix[1:].upper()
        if image_format == "JPG":
            image_format = "JPEG"

        if image_format == "PNG":
            image = image.convert("RGBA")

        image.save(output_path, format=image_format, quality=95)
        return output_path

    except KeyError as e:
        raise ValueError(f"Unsupported image format: {output_path.suffix}") from e
    except Exception as e:
        raise IOError(f"Error generating image: {str(e)}") from e
