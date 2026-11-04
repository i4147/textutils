import zipfile
from pathlib import Path
from typing import Dict, List, TypeVar, Union

from .base import BaseValidator, ValidationResult

T = TypeVar("T", bound="OfficeValidator")


class OfficeValidator(BaseValidator):
    MIME_TYPES: Dict[str, List[str]] = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
        "application/vnd.oasis.opendocument.text": [".odt"],
        "application/vnd.oasis.opendocument.spreadsheet": [".ods"],
        "application/vnd.oasis.opendocument.presentation": [".odp"],
        "application/msword": [".doc"],
        "application/vnd.ms-excel": [".xls"],
        "application/vnd.ms-powerpoint": [".ppt"],
    }

    EXTENSIONS: List[str] = [
        ".docx",
        ".xlsx",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".doc",
        ".xls",
        ".ppt",
    ]

    def __init__(self) -> None:
        super().__init__(self.MIME_TYPES, self.EXTENSIONS)

    def validate(self, file_path: Union[str, Path]) -> ValidationResult:
        file_path = Path(file_path)

        if not file_path.exists() or not file_path.is_file():
            return ValidationResult(
                valid=False,
                messages=[f"File does not exist or is not a file: {file_path}"],
            )

        ext = file_path.suffix.lower()
        if ext not in self.EXTENSIONS:
            return ValidationResult(valid=False, messages=[f"Unsupported office document extension: {ext}"])

        if ext in (".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"):
            return self._validate_office_open_xml(file_path)

        return self._validate_legacy_office(file_path)

    def _validate_office_open_xml(self, file_path: Path) -> ValidationResult:
        try:
            if not zipfile.is_zipfile(file_path):
                return ValidationResult(
                    valid=False,
                    messages=[f"Not a ZIP archive: {file_path}"],
                )

            with zipfile.ZipFile(file_path, "r") as zf:
                file_list = zf.namelist()

                required_files = {
                    ".docx": [
                        "[Content_Types].xml",
                        "word/document.xml",
                    ],
                    ".xlsx": [
                        "[Content_Types].xml",
                        "xl/workbook.xml",
                    ],
                    ".pptx": [
                        "[Content_Types].xml",
                        "ppt/presentation.xml",
                    ],
                    ".odt": [
                        "mimetype",
                        "content.xml",
                    ],
                    ".ods": [
                        "mimetype",
                        "content.xml",
                    ],
                    ".odp": [
                        "mimetype",
                        "content.xml",
                    ],
                }

                ext = file_path.suffix.lower()
                if ext in required_files:
                    for req_file in required_files[ext]:
                        if req_file not in file_list:
                            if not any(f.lower() == req_file.lower() for f in file_list):
                                msg = f"Missing required file in {ext} archive: {req_file}"
                                return ValidationResult(valid=False, messages=[msg])

            return ValidationResult(valid=True)

        except Exception as e:
            error_msg = f"Error validating office document {file_path}: {str(e)}"
            return ValidationResult(valid=False, messages=[error_msg])

    def _validate_legacy_office(self, file_path: Path) -> ValidationResult:
        try:
            if file_path.stat().st_size == 0:
                return ValidationResult(valid=False, messages=[f"File is empty: {file_path}"])

            with open(file_path, "rb") as f:
                header = f.read(8)

                if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
                    return ValidationResult(valid=True)

                if header.startswith(b"PK\x03\x04"):
                    return ValidationResult(
                        valid=False,
                        messages=[f"File appears to be an OOXML/ODF file with wrong extension: {file_path}"],
                    )

                return ValidationResult(valid=False, messages=[f"Invalid office document: {file_path}"])

        except Exception as e:
            return ValidationResult(
                valid=False,
                messages=[f"Error validating legacy office document {file_path}: {str(e)}"],
            )

    def _check_legacy_office(self, file_path: Path) -> ValidationResult:
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
                if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
                    return ValidationResult(
                        is_valid=True,
                        message=(f"Valid legacy office document: {file_path.suffix}"),
                    )
                return ValidationResult(is_valid=False, message="Not a valid legacy office document")

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=(f"Error validating legacy office document {file_path}: {str(e)}"),
            )


class DocxValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    }
    EXTENSIONS = [".docx"]


class XlsxValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    }
    EXTENSIONS = [".xlsx"]


class PptxValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
    }
    EXTENSIONS = [".pptx"]


class OdtValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.oasis.opendocument.text": [".odt"],
    }
    EXTENSIONS = [".odt"]


class OdsValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.oasis.opendocument.spreadsheet": [".ods"],
    }
    EXTENSIONS = [".ods"]


class OdpValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.oasis.opendocument.presentation": [".odp"],
    }
    EXTENSIONS = [".odp"]


class DocValidator(OfficeValidator):
    MIME_TYPES = {
        "application/msword": [".doc"],
    }
    EXTENSIONS = [".doc"]


class XlsValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.ms-excel": [".xls"],
    }
    EXTENSIONS = [".xls"]


class PptValidator(OfficeValidator):
    MIME_TYPES = {
        "application/vnd.ms-powerpoint": [".ppt"],
    }
    EXTENSIONS = [".ppt"]
