from pathlib import Path
from typing import Any, Union

from PIL import Image, ImageDraw

from ...generators.base import FileGenerator
from ...generators.registration import register_generator
from ...utils.file_utils import ensure_directory
from ...utils.image_utils import (
    create_blank_image,
    draw_text_on_image,
    load_font,
    save_image,
)
from ...validators.base import ValidationResult

FONT_SIZES = {
    "small": (100, 36),
    "medium": (200, 48),
    "large": (300, 60),
    "xlarge": (400, 72),
}

DEFAULT_BG_COLOR = "#f0f0f0"
DEFAULT_TEXT_COLOR = "#333333"
DEFAULT_PADDING = 40


def generate_jpg(
    content: str,
    output_path: Path,
    **kwargs: Any,
) -> Path:
    if not content or not isinstance(content, str):
        raise ValueError("Content must be a non-empty string")

    output_path = Path(output_path)
    ensure_directory(output_path.parent)

    size = kwargs.get("size")
    bg_color = kwargs.get("bg_color", DEFAULT_BG_COLOR)
    text_color = kwargs.get("text_color", DEFAULT_TEXT_COLOR)
    font_path = kwargs.get("font_path")
    font_size = kwargs.get("font_size")
    padding = kwargs.get("padding", DEFAULT_PADDING)
    align = kwargs.get("align", "center")
    valign = kwargs.get("valign", "middle")
    quality = max(1, min(100, int(kwargs.get("quality", 85))))
    optimize = bool(kwargs.get("optimize", True))
    progressive = bool(kwargs.get("progressive", True))
    shadow = bool(kwargs.get("shadow", False))
    border = bool(kwargs.get("border", False))
    border_color = kwargs.get("border_color", "#000000")
    border_width = max(1, int(kwargs.get("border_width", 1)))
    shadow_color = kwargs.get("shadow_color", "#00000080")
    shadow_offset = kwargs.get("shadow_offset", (2, 2))
    line_spacing = max(0, int(kwargs.get("line_spacing", 4)))
    max_width = kwargs.get("max_width")
    auto_resize = bool(kwargs.get("auto_resize", True))
    dpi = max(1, int(kwargs.get("dpi", 72)))

    if size is None:
        content_length = len(content)
        if content_length <= 50:
            size = FONT_SIZES["small"]
        elif content_length <= 200:
            size = FONT_SIZES["medium"]
        elif content_length <= 500:
            size = FONT_SIZES["large"]
        else:
            size = FONT_SIZES["xlarge"]

    width, height = map(int, size)

    if max_width is None and auto_resize:
        max_width = int(width * 0.8)

    temp_img = create_blank_image(width, height, bg_color)
    _ = ImageDraw.Draw(temp_img)

    if font_size is None:
        font_size = 24
        if len(content) > 500:
            font_size = 16
        elif len(content) > 200:
            font_size = 20
        elif len(content) > 50:
            font_size = 24
        else:
            font_size = 36

    _ = load_font(font_path, font_size)

    def get_text_dimensions(text, font, max_width=None):
        if not text:
            return (0, 0)

        if "\n" in text or (max_width and font.getlength(text) > max_width):
            lines = []
            for line in text.split("\n"):
                if not line.strip():
                    lines.append("")
                    continue

                if max_width:
                    words = line.split(" ")
                    current_line = []

                    for word in words:
                        test_line = " ".join(current_line + [word])
                        if font.getlength(test_line) <= max_width:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(" ".join(current_line))
                            current_line = [word]

                    if current_line:
                        lines.append(" ".join(current_line))
                else:
                    lines.append(line)

                total_height = 0
                max_line_width = 0
                line_heights = []

                for line in lines:
                    bbox = font.getbbox(line)
                    line_width = bbox[2] - bbox[0]
                    line_height = bbox[3] - bbox[1]

                    max_line_width = max(max_line_width, line_width)
                    line_heights.append(line_height)
                    total_height += line_height + line_spacing

                if lines:
                    total_height -= line_spacing

                return (max_line_width, total_height)
            else:
                bbox = font.getbbox(text)
                return (bbox[2] - bbox[0], bbox[3] - bbox[1])

        text_width, text_height = get_text_dimensions(content, font, max_width)

        if "width" not in locals():
            width = 800
        if "height" not in locals():
            height = 600

        if auto_resize:
            required_width = text_width + 2 * padding
            required_height = text_height + 2 * padding

            min_width, min_height = 100, 50
            required_width = max(required_width, min_width)
            required_height = max(required_height, min_height)

            if required_width > width or required_height > height:
                width = max(width, required_width)
                height = max(height, required_height)

        img = create_blank_image(width, height, bg_color)

        x = width // 2
        y = height // 2

        img = draw_text_on_image(
            image=img,
            text=content,
            position=(x, y),
            font=font,
            color=text_color,
            bg_color=bg_color if border else None,
            align=align,
            valign=valign,
            padding=padding,
            shadow=shadow,
            shadow_color=shadow_color,
            shadow_offset=shadow_offset,
            border=border,
            border_color=border_color,
            border_width=border_width,
        )

        save_image(
            img,
            output_path,
            format="JPEG",
            quality=quality,
            optimize=optimize,
            progressive=progressive,
            dpi=(dpi, dpi),
        )

        return output_path


class JpgGenerator(FileGenerator):
    @classmethod
    def generate(cls, content: str, output_path: Path, **kwargs: Any) -> Path:
        return generate_jpg(content, output_path, **kwargs)

    @classmethod
    def validate(cls, file_path: Union[str, Path]) -> "ValidationResult":
        from ...validators.image_validator import JpegValidator

        return JpegValidator.validate(file_path)


@register_generator(["jpg", "jpeg"])
def generate_jpg_file(
    content: str,
    output_path: Path,
    **kwargs: Any,
) -> Path:
    return generate_jpg(content, output_path, **kwargs)
