import base64
import io
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from .file_utils import ensure_directory


def create_blank_image(width: int = 800, height: int = 600, color: str = "#FFFFFF", mode: str = "RGB") -> Image.Image:
    try:
        bg_color = ImageColor.getrgb(color)
        if mode == "RGBA":
            if len(bg_color) == 3:
                bg_color = bg_color + (255,)
    except (ValueError, AttributeError):
        bg_color = (255, 255, 255) if mode == "RGB" else (255, 255, 255, 255)

    return Image.new(mode, (width, height), color=bg_color)


def load_font(font_path: Optional[str] = None, font_size: int = 12) -> ImageFont.FreeTypeFont:
    try:
        if font_path:
            return ImageFont.truetype(font_path, font_size)

        try:
            return ImageFont.truetype("Arial.ttf", font_size)
        except IOError:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", font_size)
            except IOError:
                return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def get_text_size(
    text: str,
    font: ImageFont.FreeTypeFont,
    spacing: int = 4,
    max_width: Optional[int] = None,
) -> Tuple[int, int]:
    if not text:
        return (0, 0)

    if "\n" in text or (max_width and font.getlength(text) > max_width):
        return get_multiline_text_size(text, font, spacing, max_width)

    left, top, right, bottom = font.getbbox(text)
    return (right - left, bottom - top)


def get_multiline_text_size(
    text: str,
    font: ImageFont.FreeTypeFont,
    spacing: int = 4,
    max_width: Optional[int] = None,
) -> Tuple[int, int]:
    if not text:
        return (0, 0)

    lines = text.split("\n")

    processed_lines = []
    for line in lines:
        if not line.strip():
            processed_lines.append("")
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
                        processed_lines.append(" ".join(current_line))
                    current_line = [word]

            if current_line:
                processed_lines.append(" ".join(current_line))
        else:
            processed_lines.append(line)

    total_height = 0
    max_line_width = 0
    line_heights = []

    for i, line in enumerate(processed_lines):
        left, top, right, bottom = font.getbbox(line)
        line_width = right - left
        line_height = bottom - top + (spacing if i < len(processed_lines) - 1 else 0)

        max_line_width = max(max_line_width, line_width)
        line_heights.append(line_height)
        total_height += line_height

    return (max_line_width, total_height)


def draw_text_on_image(
    image: Image.Image,
    text: str,
    position: Tuple[int, int] = (0, 0),
    font: Optional[ImageFont.FreeTypeFont] = None,
    font_size: int = 12,
    font_path: Optional[str] = None,
    color: str = "#000000",
    bg_color: Optional[str] = None,
    align: str = "left",
    valign: str = "top",
    max_width: Optional[int] = None,
    line_spacing: int = 4,
    padding: int = 10,
    rotate: int = 0,
    shadow: bool = False,
    shadow_color: str = "#00000080",
    shadow_offset: Tuple[int, int] = (2, 2),
    border: bool = False,
    border_color: str = "#000000",
    border_width: int = 1,
) -> Image.Image:
    if not text:
        return image

    if font is None:
        font = load_font(font_path, font_size)

    draw = ImageDraw.Draw(image)

    lines = []
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
    else:
        lines = [text]

    line_heights = []
    max_line_width = 0

    for line in lines:
        left, top, right, bottom = font.getbbox(line)
        line_width = right - left
        line_height = bottom - top

        max_line_width = max(max_line_width, line_width)
        line_heights.append(line_height)

    total_height = sum(line_heights) + (len(lines) - 1) * line_spacing

    x, y = position

    if align == "center":
        x -= max_line_width // 2
    elif align == "right":
        x -= max_line_width

    if valign == "middle":
        y -= total_height // 2
    elif valign == "bottom":
        y -= total_height

    current_y = y

    for i, line in enumerate(lines):
        line_height = line_heights[i]
        line_left = x

        if align == "center":
            left, top, right, bottom = font.getbbox(line)
            line_width = right - left
            line_left = x + (max_line_width - line_width) // 2
        elif align == "right":
            left, top, right, bottom = font.getbbox(line)
            line_width = right - left
            line_left = x + (max_line_width - line_width)

        if shadow:
            shadow_pos = (line_left + shadow_offset[0], current_y + shadow_offset[1])
            draw.text(shadow_pos, line, font=font, fill=shadow_color)

        if border and border_width > 0:
            for x_offset in [-border_width, 0, border_width]:
                for y_offset in [-border_width, 0, border_width]:
                    if x_offset == 0 and y_offset == 0:
                        continue
                    pos = (line_left + x_offset, current_y + y_offset)
                    draw.text(pos, line, font=font, fill=border_color)

        draw.text((line_left, current_y), line, font=font, fill=color)

        current_y += line_height + line_spacing

    return image


def create_text_image(
    text: str,
    size: Tuple[int, int] = (800, 400),
    bg_color: str = "#FFFFFF",
    text_color: str = "#000000",
    font_size: int = 24,
    font_path: Optional[str] = None,
    align: str = "center",
    valign: str = "middle",
    padding: int = 20,
    rotate: int = 0,
    shadow: bool = False,
    shadow_color: str = "#00000080",
    shadow_offset: Tuple[int, int] = (2, 2),
    border: bool = False,
    border_color: str = "#000000",
    border_width: int = 1,
) -> Image.Image:
    image = create_blank_image(size[0], size[1], bg_color)

    x = size[0] // 2
    y = size[1] // 2

    image = draw_text_on_image(
        image=image,
        text=text,
        position=(x, y),
        font_size=font_size,
        font_path=font_path,
        color=text_color,
        align=align,
        valign=valign,
        padding=padding,
        rotate=rotate,
        shadow=shadow,
        shadow_color=shadow_color,
        shadow_offset=shadow_offset,
        border=border,
        border_color=border_color,
        border_width=border_width,
    )

    return image


def save_image(
    image: Image.Image,
    output_path: Union[str, Path],
    format: Optional[str] = None,
    quality: int = 95,
    **kwargs,
) -> bool:
    try:
        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        if format is None:
            ext = output_path.suffix.lower()
            if ext in [".jpg", ".jpeg", ".jpe", ".jfif", ".jif"]:
                format = "JPEG"
            elif ext == ".png":
                format = "PNG"
            elif ext == ".gif":
                format = "GIF"
            elif ext in [".tif", ".tiff"]:
                format = "TIFF"
            elif ext == ".webp":
                format = "WEBP"
            elif ext == ".bmp":
                format = "BMP"
            else:
                format = "PNG"

        save_kwargs = kwargs.copy()

        if format.upper() == "JPEG":
            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            save_kwargs.setdefault("quality", quality)
            save_kwargs.setdefault("optimize", True)
            save_kwargs.setdefault("progressive", True)

        elif format.upper() == "PNG":
            save_kwargs.setdefault("optimize", True)
            if "compress_level" not in save_kwargs:
                save_kwargs["compress_level"] = 6

        elif format.upper() == "WEBP":
            save_kwargs.setdefault("quality", quality)
            save_kwargs.setdefault("method", 6)

        image.save(output_path, format=format, **save_kwargs)
        return True

    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def image_to_base64(image: Image.Image, format: str = "PNG", **kwargs) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format=format, **kwargs)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def base64_to_image(data: str) -> Optional[Image.Image]:
    try:
        if "," in data:
            data = data.split(",", 1)[1]
        return Image.open(io.BytesIO(base64.b64decode(data)))
    except Exception:
        return None


def resize_image(
    image: Image.Image,
    size: Tuple[int, int],
    resample: int = Image.Resampling.LANCZOS,
    keep_aspect_ratio: bool = True,
    bg_color: str = "#FFFFFF",
) -> Image.Image:
    if not keep_aspect_ratio:
        return image.resize(size, resample=resample)

    orig_width, orig_height = image.size
    target_width, target_height = size

    width_ratio = target_width / orig_width
    height_ratio = target_height / orig_height

    if width_ratio < height_ratio:
        new_width = target_width
        new_height = int(orig_height * width_ratio)
    else:
        new_height = target_height
        new_width = int(orig_width * height_ratio)

    resized_image = image.resize((new_width, new_height), resample=resample)

    if new_width != target_width or new_height != target_height:
        result = create_blank_image(target_width, target_height, bg_color, "RGBA")
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        result.paste(resized_image, (x, y))
        return result

    return resized_image


def apply_filter(image: Image.Image, filter_name: str, **kwargs) -> Optional[Image.Image]:
    filter_name = filter_name.lower()

    if filter_name == "blur":
        radius = kwargs.get("radius", 2)
        return image.filter(ImageFilter.GaussianBlur(radius))

    elif filter_name == "sharpen":
        return image.filter(ImageFilter.SHARPEN)

    elif filter_name == "edge_enhance":
        return image.filter(ImageFilter.EDGE_ENHANCE)

    elif filter_name == "emboss":
        return image.filter(ImageFilter.EMBOSS)

    elif filter_name == "contour":
        return image.filter(ImageFilter.CONTOUR)

    elif filter_name == "detail":
        return image.filter(ImageFilter.DETAIL)

    elif filter_name == "smooth":
        return image.filter(ImageFilter.SMOOTH)

    elif filter_name == "grayscale":
        return image.convert("L")

    elif filter_name == "sepia":
        if image.mode != "RGB":
            image = image.convert("RGB")

        sepia_matrix = (0.393, 0.769, 0.189, 0.349, 0.686, 0.168, 0.272, 0.534, 0.131)
        sepia_image = image.convert("RGB", sepia_matrix)
        return sepia_image

    else:
        raise ValueError(f"Unknown filter: {filter_name}")
