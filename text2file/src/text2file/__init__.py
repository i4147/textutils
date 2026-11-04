from importlib.metadata import PackageNotFoundError, version

from .cli import cli
from .generators import (
    FileValidator,
    ImageFileValidator,
    PDFFileValidator,
    TextFileValidator,
    ValidationResult,
    cleanup_invalid_files,
    generate_file,
    get_validator,
    validate_file,
)

try:
    __version__ = version("text2file")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "cli",
    "FileValidator",
    "TextFileValidator",
    "ImageFileValidator",
    "PDFFileValidator",
    "ValidationResult",
    "cleanup_invalid_files",
    "generate_file",
    "validate_file",
    "get_validator",
    "__version__",
]
