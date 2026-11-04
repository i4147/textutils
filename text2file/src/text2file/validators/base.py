from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T", bound="ValidationResult")


@dataclass
class ValidationResult:
    is_valid: bool
    message: str
    details: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        return self.is_valid


class BaseValidator(ABC):
    @classmethod
    @abstractmethod
    def validate(cls, file_path: str) -> ValidationResult:
        raise NotImplementedError("Subclasses must implement validate()")

    @classmethod
    def is_valid(cls, file_path: str) -> bool:
        return bool(cls.validate(file_path))


def get_validator(file_path: str) -> Type[BaseValidator]:
    from ..generators import get_generator
    from . import (
        archive_validator,
        image_validator,
        office_validator,
        pdf_validator,
        text_validator,
        video_validator,
    )

    validators = {
        "txt": text_validator.TextFileValidator,
        "md": text_validator.TextFileValidator,
        "html": text_validator.HtmlFileValidator,
        "css": text_validator.CssFileValidator,
        "js": text_validator.JavaScriptFileValidator,
        "py": text_validator.PythonFileValidator,
        "json": text_validator.JsonFileValidator,
        "csv": text_validator.CsvFileValidator,
        "xml": text_validator.XmlFileValidator,
        "yaml": text_validator.YamlFileValidator,
        "yml": text_validator.YamlFileValidator,
        "jpg": image_validator.JpegValidator,
        "jpeg": image_validator.JpegValidator,
        "png": image_validator.PngValidator,
        "gif": image_validator.GifValidator,
        "bmp": image_validator.BmpValidator,
        "webp": image_validator.WebPValidator,
        "svg": image_validator.SvgValidator,
        "zip": archive_validator.ZipValidator,
        "tar": archive_validator.TarValidator,
        "tar.gz": archive_validator.TarGzValidator,
        "tgz": archive_validator.TarGzValidator,
        "tar.bz2": archive_validator.TarBz2Validator,
        "tbz2": archive_validator.TarBz2Validator,
        "pdf": pdf_validator.PdfValidator,
        "docx": office_validator.DocxValidator,
        "xlsx": office_validator.XlsxValidator,
        "pptx": office_validator.PptxValidator,
        "odt": office_validator.OdtValidator,
        "ods": office_validator.OdsValidator,
        "odp": office_validator.OdpValidator,
        "mp4": video_validator.Mp4Validator,
        "avi": video_validator.AviValidator,
        "mov": video_validator.MovValidator,
        "mkv": video_validator.MkvValidator,
        "webm": video_validator.WebmValidator,
    }

    ext = Path(file_path).suffix.lstrip(".").lower()

    if ext in ["gz", "bz2"] and len(parts := Path(file_path).suffixes) > 1:
        ext = f"{parts[-2].lstrip('.')}{parts[-1]}"

    return validators.get(ext, BaseValidator)
