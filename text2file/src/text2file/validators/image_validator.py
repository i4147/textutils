import imghdr
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError

from .base import BaseValidator, ValidationResult


class ImageValidator(BaseValidator):
    FORMAT: Optional[str] = None

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            path = Path(file_path)
            if not path.exists():
                return ValidationResult(is_valid=False, message=f"File not found: {file_path}")

            if not path.is_file():
                return ValidationResult(is_valid=False, message=f"Not a file: {file_path}")

            if cls.FORMAT and path.suffix.lower()[1:] != cls.FORMAT.lower():
                return ValidationResult(
                    is_valid=False,
                    message=(f"Expected {cls.FORMAT.upper()} file, got {path.suffix}"),
                )

            detected_format = imghdr.what(file_path)
            if detected_format is None:
                return ValidationResult(is_valid=False, message="File is not a recognized image format")

            if cls.FORMAT and detected_format.lower() != cls.FORMAT.lower():
                return ValidationResult(
                    is_valid=False,
                    message=(f"File is not a {cls.FORMAT.upper()} image (detected as {detected_format.upper()})"),
                )

            try:
                with Image.open(file_path) as img:
                    img.verify()
                    width, height = img.size

                    if width == 0 or height == 0:
                        return ValidationResult(
                            is_valid=False,
                            message=f"Invalid image dimensions: {width}x{height}",
                            details={"width": width, "height": height},
                        )

                    return ValidationResult(is_valid=True, message="Valid image file")
            except UnidentifiedImageError as e:
                return ValidationResult(
                    is_valid=False,
                    message=f"Invalid or corrupted image: {str(e)}",
                )
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    message=f"Error validating image: {str(e)}",
                    details={"error": str(e)},
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error processing image file: {str(e)}",
                details={"error": str(e)},
            )


class JpegValidator(ImageValidator):
    FORMAT = "jpeg"

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        result = super().validate(file_path)
        if not result.is_valid:
            return result

        return result


class PngValidator(ImageValidator):
    FORMAT = "png"

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        result = super().validate(file_path)
        if not result.is_valid:
            return result

        return result


class GifValidator(ImageValidator):
    FORMAT = "gif"

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        result = super().validate(file_path)
        if not result.is_valid:
            return result

        try:
            with Image.open(file_path) as img:
                if hasattr(img, "n_frames") and img.n_frames > 1:
                    result.details = result.details or {}
                    result.details["frames"] = img.n_frames
                    result.message = f"Valid animated GIF with {img.n_frames} frames: {img.width}x{img.height} pixels"
        except Exception:
            pass

        return result


class BmpValidator(ImageValidator):
    FORMAT = "bmp"


class WebPValidator(ImageValidator):
    FORMAT = "webp"


class SvgValidator(ImageValidator):
    FORMAT = "svg"

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        path = Path(file_path)
        if not path.exists():
            return ValidationResult(is_valid=False, message=f"File not found: {file_path}")

        if path.suffix.lower() != ".svg":
            return ValidationResult(is_valid=False, message=f"Not an SVG file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(1024).lower()
                if "<!doctype svg" not in content and "<svg" not in content:
                    return ValidationResult(
                        is_valid=False,
                        message="File does not appear to be a valid SVG (missing SVG root element)",
                    )

                return ValidationResult(
                    is_valid=True,
                    message="File appears to be a valid SVG",
                    details={"size": path.stat().st_size},
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating SVG file: {str(e)}",
                details={"error": str(e)},
            )
