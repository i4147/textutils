import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .registration import GeneratorFunc
from .registration import get_generator as _get_generator
from .registration import get_supported_extensions, register_generator
from .validators import (
    FileValidator,
    ImageFileValidator,
    PDFFileValidator,
    TextFileValidator,
    ValidationResult,
    cleanup_invalid_files,
)
from .validators import get_validator as _get_validator
from .validators import validate_file

register_generator = register_generator
get_generator = _get_generator


def SUPPORTED_EXTENSIONS():
    return get_supported_extensions()


get_validator = _get_validator

__all__ = [
    "FileValidator",
    "TextFileValidator",
    "ImageFileValidator",
    "PDFFileValidator",
    "ValidationResult",
    "cleanup_invalid_files",
    "generate_file",
    "get_generator",
    "get_validator",
    "register_generator",
    "validate_file",
    "GeneratorFunc",
    "SUPPORTED_EXTENSIONS",
]


_DEFAULT_OUTPUT_DIR = Path.cwd()


def generate_file(
    content: str,
    extension: str,
    output_dir: Optional[Path] = None,
    prefix: str = "generated",
) -> Path:
    generator = get_generator(extension)
    if generator is None:
        raise ValueError(f"No generator found for extension: {extension}")

    if output_dir is None:
        output_dir = _DEFAULT_OUTPUT_DIR
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{extension.lstrip('.')}"
    output_path = output_dir / filename

    try:
        generated_path = generator(content, output_path)
        return generated_path
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        raise IOError(f"Error generating {extension} file: {str(e)}") from e


try:

    def get_supported_extensions_with_reload():
        return get_supported_extensions()

    from .text import generate_text_file

    register_generator(["txt", "md", "html", "css", "js", "py", "json", "csv"])(generate_text_file)

    from .archives import generate_zip_file, generate_tar_file

    register_generator(["zip"])(generate_zip_file)
    register_generator(["tar"])(generate_tar_file)
    register_generator(["tar.gz", "tgz"])(generate_tar_file)

    from .image.svg_generator import generate_svg

    register_generator(["svg"])(generate_svg)

    from .pdf import generate_pdf_file

    register_generator(["pdf"])(generate_pdf_file)

    from .config import ConfigGenerator

    from .image import *

    from .image_set import ImageSetGenerator
    from .office import *
    from .video import *

    try:
        from .excel import register as register_excel_generator

        register_excel_generator()
    except ImportError as e:
        print(f"Warning: Excel generation not available: {e}", file=sys.stderr)

    __all__.append("ImageSetGenerator")

except ImportError as e:
    print(f"Error importing generators: {e}", file=sys.stderr)
    raise
