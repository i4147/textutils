import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type


@dataclass
class ValidationResult:
    is_valid: bool
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class FileValidator:
    @classmethod
    def validate_file(cls, file_path: str) -> ValidationResult:
        if not os.path.exists(file_path):
            return ValidationResult(is_valid=False, message=f"File does not exist: {file_path}")

        if not os.path.isfile(file_path):
            return ValidationResult(is_valid=False, message=f"Path is not a file: {file_path}")

        return cls._validate(file_path)

    @classmethod
    def _validate(cls, file_path: str) -> ValidationResult:
        try:
            with open(file_path, "rb") as f:
                first_byte = f.read(1)
                if not first_byte:
                    return ValidationResult(is_valid=False, message="File is empty")
            return ValidationResult(is_valid=True, message="File is valid")
        except Exception as e:
            return ValidationResult(is_valid=False, message=f"Error validating file: {str(e)}")


class TextFileValidator(FileValidator):
    @classmethod
    def _validate(cls, file_path: str) -> ValidationResult:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not all(ord(c) >= 32 or c in "\n\r\t" for c in content):
                    return ValidationResult(is_valid=False, message="File contains non-printable characters")
            return ValidationResult(is_valid=True, message="Text file is valid")
        except UnicodeDecodeError:
            return ValidationResult(is_valid=False, message="File is not valid UTF-8 text")


class ImageFileValidator(FileValidator):
    @classmethod
    def _validate(cls, file_path: str) -> ValidationResult:
        try:
            import imghdr

            from PIL import Image

            image_type = imghdr.what(file_path)
            if not image_type:
                return ValidationResult(is_valid=False, message="File is not a recognized image format")

            try:
                with Image.open(file_path) as img:
                    img.verify()
                return ValidationResult(is_valid=True, message=f"Valid {image_type.upper()} image")
            except Exception as e:
                return ValidationResult(is_valid=False, message=f"Invalid image file: {str(e)}")

        except ImportError:
            return super()._validate(file_path)


class PDFFileValidator(FileValidator):
    @classmethod
    def _validate(cls, file_path: str) -> ValidationResult:
        try:
            from PyPDF2 import PdfReader

            with open(file_path, "rb") as f:
                try:
                    pdf = PdfReader(f)
                    if pdf.is_encrypted:
                        return ValidationResult(is_valid=False, message="PDF is encrypted")
                    if len(pdf.pages) == 0:
                        return ValidationResult(is_valid=False, message="PDF has no pages")
                    return ValidationResult(is_valid=True, message=f"Valid PDF with {len(pdf.pages)} pages")
                except Exception as e:
                    return ValidationResult(is_valid=False, message=f"Invalid PDF file: {str(e)}")

        except ImportError:
            return super()._validate(file_path)


VALIDATORS = {
    ".txt": TextFileValidator,
    ".csv": TextFileValidator,
    ".json": TextFileValidator,
    ".xml": TextFileValidator,
    ".jpg": ImageFileValidator,
    ".jpeg": ImageFileValidator,
    ".png": ImageFileValidator,
    ".gif": ImageFileValidator,
    ".bmp": ImageFileValidator,
    ".pdf": PDFFileValidator,
}


def get_validator(file_path: str) -> Type["FileValidator"]:
    ext = os.path.splitext(file_path)[1].lower()
    return VALIDATORS.get(ext, FileValidator)


def validate_file(file_path: str) -> ValidationResult:
    validator = get_validator(file_path)
    return validator.validate_file(file_path)


def cleanup_invalid_files(directory: str, recursive: bool = False) -> Dict[str, ValidationResult]:
    results = {}
    path = Path(directory)

    pattern = "**/*" if recursive else "*"

    for file_path in path.glob(pattern):
        if file_path.is_file():
            result = validate_file(str(file_path))
            results[str(file_path)] = result

            if not result.is_valid:
                try:
                    file_path.unlink()
                    result.message = f"{result.message} (deleted)"
                except Exception as e:
                    result.message = f"{result.message} (failed to delete: {str(e)})"

    return results
