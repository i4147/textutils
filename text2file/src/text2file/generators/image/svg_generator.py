from pathlib import Path
from typing import Any

from ...generators.registration import register_generator_directly
from ...utils.file_utils import ensure_directory


def _create_svg_content(content: str, width: int = 200, height: int = 100) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" version="1.1"
     viewBox="0 0 {width} {height}" 
     xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="white"/>
  <text x="50%" y="50%"
        font-family="Arial, sans-serif"
        font-size="14"
        text-anchor="middle"
        dominant-baseline="middle"
        fill="black">
    {content}
  </text>
</svg>"""


def generate_svg(content: str, output_path: Path, width: int = 200, height: int = 100, **kwargs: Any) -> Path:
    svg_content = _create_svg_content(content, width, height)

    if output_path.parent:
        ensure_directory(output_path.parent)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(svg_content)

    return output_path


register_generator_directly(["svg"], generate_svg)
