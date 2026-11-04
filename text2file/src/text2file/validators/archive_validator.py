import bz2
import gzip
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseValidator, ValidationResult


class ArchiveValidator(BaseValidator):
    FORMAT: Optional[str] = None

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            path = Path(file_path)
            if not path.exists():
                return ValidationResult(is_valid=False, message=f"File not found: {file_path}")

            if not path.is_file():
                return ValidationResult(is_valid=False, message=f"Not a file: {file_path}")

            if cls.FORMAT and not cls._matches_format(path, cls.FORMAT):
                return ValidationResult(
                    is_valid=False,
                    message=(f"Expected {cls.FORMAT.upper()} file, got {path.suffix}"),
                )

            return cls._validate_archive(file_path)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error processing archive file: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _matches_format(cls, path: Path, format_str: str) -> bool:
        if format_str == "tar.gz":
            return path.suffixes == [".tar", ".gz"] or path.suffix == ".tgz"
        if format_str == "tar.bz2":
            return path.suffixes == [".tar", ".bz2"] or path.suffix == ".tbz2"
        return path.suffix.lower() == f".{format_str}"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        raise NotImplementedError("Subclasses must implement _validate_archive()")

    @classmethod
    def _get_archive_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Subclasses must implement _get_archive_contents()")


class ZipValidator(ArchiveValidator):
    FORMAT = "zip"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                test_result = zip_ref.testzip()
                if test_result is not None:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Corrupt file in ZIP archive: {test_result}",
                        details={"corrupt_file": test_result},
                    )

                contents = cls._get_archive_contents(file_path)

                return ValidationResult(
                    is_valid=True,
                    message=f"Valid ZIP archive with {len(contents)} files",
                    details={
                        "file_count": len(contents),
                        "total_size": sum(f["size"] for f in contents),
                        "files": contents,
                    },
                )

        except zipfile.BadZipFile as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid ZIP file: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _get_archive_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            return [
                {
                    "filename": info.filename,
                    "file_size": info.file_size,
                    "compress_size": info.compress_size,
                    "is_dir": info.is_dir(),
                    "modified": info.date_time,
                }
                for info in zip_ref.infolist()
            ]


class TarValidator(ArchiveValidator):
    FORMAT = "tar"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        try:
            with tarfile.open(file_path, "r:*") as tar_ref:
                tar_members = tar_ref.getmembers()

                contents = cls._get_archive_contents(file_path)

                return ValidationResult(
                    is_valid=True,
                    message=f"Valid TAR archive with {len(contents)} files",
                    details={
                        "file_count": len(contents),
                        "total_size": sum(f["size"] for f in contents),
                        "files": contents,
                    },
                )

        except tarfile.TarError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid TAR file: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _get_archive_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        contents = []
        with tarfile.open(file_path, "r:*") as tar_ref:
            for member in tar_ref.getmembers():
                contents.append({
                    "filename": member.name,
                    "size": member.size,
                    "modified": member.mtime,
                    "is_dir": member.isdir(),
                    "mode": member.mode,
                    "user": member.uname if hasattr(member, "uname") else "",
                    "group": member.gname if hasattr(member, "gname") else "",
                })
        return contents


class TarGzValidator(TarValidator):
    FORMAT = "tar.gz"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        try:
            with gzip.open(file_path, "rb") as f:
                f.read(1)
        except (gzip.BadGzipFile, OSError) as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid gzip file: {str(e)}",
                details={"error": str(e)},
            )

        return super()._validate_archive(file_path)


class TarBz2Validator(TarValidator):
    FORMAT = "tar.bz2"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        try:
            with bz2.open(file_path, "rb") as f:
                f.read(1)
        except (OSError, EOFError) as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid bzip2 file: {str(e)}",
                details={"error": str(e)},
            )

        return super()._validate_archive(file_path)


class GzipValidator(ArchiveValidator):
    FORMAT = "gz"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        try:
            with gzip.open(file_path, "rb") as f:
                f.read(1)

            with gzip.open(file_path, "rb") as f:
                original_filename = f.name

            return ValidationResult(
                is_valid=True,
                message="Valid gzip file",
                details={
                    "original_filename": original_filename if original_filename != file_path else None,
                    "size": Path(file_path).stat().st_size,
                },
            )

        except (gzip.BadGzipFile, OSError) as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid gzip file: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _get_archive_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        return [
            {
                "filename": Path(file_path).name,
                "size": Path(file_path).stat().st_size,
                "is_dir": False,
            }
        ]


class Bzip2Validator(ArchiveValidator):
    FORMAT = "bz2"

    @classmethod
    def _validate_archive(cls, file_path: str) -> ValidationResult:
        try:
            with bz2.open(file_path, "rb") as f:
                f.read(1)

            return ValidationResult(
                is_valid=True,
                message="Valid bzip2 file",
                details={"size": Path(file_path).stat().st_size},
            )

        except (OSError, EOFError) as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid bzip2 file: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _get_archive_contents(cls, file_path: str) -> List[Dict[str, Any]]:
        return [
            {
                "filename": Path(file_path).name,
                "size": Path(file_path).stat().st_size,
                "is_dir": False,
            }
        ]
