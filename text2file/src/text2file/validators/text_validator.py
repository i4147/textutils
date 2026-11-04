import csv
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

import yaml

from .base import BaseValidator, ValidationResult


class TextFileValidator(BaseValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for i, char in enumerate(content):
                if ord(char) < 32 and char not in "\n\r\t":
                    return ValidationResult(
                        is_valid=False,
                        message=f"File contains non-printable character at position {i}",
                        details={"position": i, "character": repr(char)},
                    )

            return ValidationResult(is_valid=True, message="File is a valid text file")

        except UnicodeDecodeError:
            return ValidationResult(is_valid=False, message="File is not valid UTF-8 text")
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating text file: {str(e)}",
                details={"error": str(e)},
            )


class JsonFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        text_result = super().validate(file_path)
        if not text_result.is_valid:
            return text_result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)
            return ValidationResult(is_valid=True, message="File is valid JSON")
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid JSON: {str(e)}",
                details={"error": str(e), "line": e.lineno, "column": e.colno},
            )


class CsvFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        text_result = super().validate(file_path)
        if not text_result.is_valid:
            return text_result

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

                if not rows:
                    return ValidationResult(is_valid=True, message="File is a valid (empty) CSV")

                num_columns = len(rows[0])
                for i, row in enumerate(rows[1:], 2):
                    if len(row) != num_columns:
                        return ValidationResult(
                            is_valid=False,
                            message=f"Row {i} has {len(row)} columns, expected {num_columns}",
                            details={
                                "row": i,
                                "found_columns": len(row),
                                "expected_columns": num_columns,
                            },
                        )

            return ValidationResult(
                is_valid=True,
                message=f"File is a valid CSV with {len(rows)} rows and {num_columns} columns",
            )

        except csv.Error as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid CSV: {str(e)}",
                details={"error": str(e)},
            )


class XmlFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        text_result = super().validate(file_path)
        if not text_result.is_valid:
            return text_result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                ET.parse(f)
            return ValidationResult(is_valid=True, message="File is valid XML")
        except ET.ParseError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid XML: {str(e)}",
                details={
                    "error": str(e),
                    "position": e.position if hasattr(e, "position") else None,
                },
            )


class YamlFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        text_result = super().validate(file_path)
        if not text_result.is_valid:
            return text_result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
            return ValidationResult(is_valid=True, message="File is valid YAML")
        except yaml.YAMLError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid YAML: {str(e)}",
                details={"error": str(e)},
            )


class HtmlFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return super().validate(file_path)

        text_result = super().validate(file_path)
        if not text_result.is_valid:
            return text_result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")

                if soup.find() is None:
                    return ValidationResult(is_valid=False, message="No valid HTML content found")

                return ValidationResult(is_valid=True, message="File is valid HTML")

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error parsing HTML: {str(e)}",
                details={"error": str(e)},
            )


class CssFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        return super().validate(file_path)


class JavaScriptFileValidator(TextFileValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        return super().validate(file_path)


class PythonFileValidator(BaseValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            text_result = TextFileValidator.validate(file_path)
            if not text_result.is_valid:
                return text_result

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    compile(f.read(), file_path, "exec")
                except SyntaxError as e:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Invalid Python syntax: {e.msg}",
                        details={
                            "line": e.lineno,
                            "column": e.offset or 0,
                            "message": e.msg,
                        },
                    )

            return ValidationResult(
                is_valid=True,
                message="Valid Python file",
                details={"lines": sum(1 for _ in open(file_path, "rb"))},
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating Python file: {str(e)}",
                details={"error": str(e)},
            )


class ShellScriptValidator(BaseValidator):
    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            text_result = TextFileValidator.validate(file_path)
            if not text_result.is_valid:
                return text_result

            if hasattr(os, "access") and os.access(file_path, os.X_OK):
                return ValidationResult(
                    is_valid=True,
                    message="Valid shell script (executable)",
                    details={"executable": True},
                )
            else:
                return ValidationResult(
                    is_valid=True,
                    message="Valid shell script (not executable)",
                    details={"executable": False},
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating shell script: {str(e)}",
                details={"error": str(e)},
            )
