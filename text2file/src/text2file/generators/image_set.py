import json
import os
from pathlib import Path
from typing import List, Optional, TypedDict, Union

from PIL import Image, ImageDraw, ImageFont

from .base import BaseGenerator


class ImageConfig(TypedDict):
    src: str
    sizes: str


class ImageSetConfig(TypedDict):
    icons: List[ImageConfig]


class ImageSetGenerator(BaseGenerator):
    @classmethod
    def generate(
        cls,
        config_path: Union[str, Path],
        output_dir: Union[str, Path],
        base_image: Optional[Union[str, Path]] = None,
        background_color: str = "#ffffff",
        text_color: str = "#000000",
        text: Optional[str] = None,
    ) -> List[Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(config_path, "r", encoding="utf-8") as f:
            config: ImageSetConfig = json.load(f)

        generated_files: List[Path] = []

        for icon in config.get("icons", []):
            try:
                width, height = map(int, icon["sizes"].lower().split("x"))
                output_path = output_dir / icon["src"]
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if base_image and os.path.exists(base_image):
                    with Image.open(base_image) as img:
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                        img.save(output_path)
                else:
                    img = Image.new("RGB", (width, height), color=background_color)
                    if text:
                        draw = ImageDraw.Draw(img)
                        try:
                            font_size = min(width, height) // 4
                            font = ImageFont.truetype("arial.ttf", font_size)
                        except IOError:
                            font = ImageFont.load_default()

                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                        position = (
                            (width - text_width) // 2,
                            (height - text_height) // 2,
                        )

                        draw.text(position, text, fill=text_color, font=font)
                    img.save(output_path)

                generated_files.append(output_path)

            except Exception as e:
                print(f"Error generating {icon.get('src')}: {str(e)}")
                continue

        return generated_files
