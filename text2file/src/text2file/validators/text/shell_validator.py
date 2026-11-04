import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ...utils.file_utils import get_file_extension, is_binary_file
from ..base import BaseValidator, ValidationResult


class ShellScriptValidator(BaseValidator):
    SHELL_SHEBANGS = [
        "#!/bin/sh",
        "#!/bin/bash",
        "#!/bin/zsh",
        "#!/bin/ksh",
        "#!/bin/dash",
        "#!/usr/bin/env bash",
        "#!/usr/bin/env sh",
        "#!/usr/bin/env zsh",
        "#!/usr/bin/env ksh",
        "#!/usr/bin/env dash",
    ]

    SHELL_EXTENSIONS = ["sh", "bash", "zsh", "ksh", "csh", "fish"]

    def _parse_shebang(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        if not content.startswith("#!"):
            return None, None

        shebang_line = content.split("\n", 1)[0].strip()
        parts = shebang_line[2:].strip().split()

        if not parts:
            return None, None

        interpreter = parts[0]
        path = parts[1] if len(parts) > 1 else None

        return interpreter, path

    def _run_shellcheck(self, filepath: Path) -> Tuple[bool, str]:
        if not shutil.which("shellcheck"):
            return False, "shellcheck is not installed"

        try:
            result = subprocess.run(
                ["shellcheck", str(filepath)],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                return True, "Shellcheck validation passed"
            return False, f"Shellcheck validation failed: {result.stderr}"

        except Exception as e:
            return False, f"Error running shellcheck: {str(e)}"

    @classmethod
    def validate(cls, file_path: Union[str, Path]) -> ValidationResult:
        file_path = Path(file_path)
        details: Dict[str, Any] = {}

        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                message=f"File not found: {file_path}",
                details=details,
            )

        ext = get_file_extension(file_path)
        if ext.lower() not in cls.SHELL_EXTENSIONS:
            details["info"] = f"Extension {ext} not in {cls.SHELL_EXTENSIONS}"

        if is_binary_file(file_path):
            return ValidationResult(
                is_valid=False,
                message=f"File appears to be binary: {file_path}",
                details=details,
            )

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ValidationResult(
                is_valid=False,
                message="File is not a valid UTF-8 text file",
                details=details,
            )

        shell_patterns = [
            r"\$\{[^}]+\}",
            r"\$[a-zA-Z_][a-zA-Z0-9_]*",
            r"`.*`",
            r"\$\(.*\)",
        ]

        pattern_matches = 0
        for pattern in shell_patterns:
            if re.search(pattern, content, re.MULTILINE):
                pattern_matches += 1

        if pattern_matches < 2:
            return ValidationResult(
                is_valid=False,
                message=(
                    f"File does not appear to be a valid shell script (found only {pattern_matches} shell patterns)"
                ),
                details=details,
            )

        is_valid, message = cls._run_shellcheck(file_path)
        if not is_valid:
            details["shellcheck_output"] = message
            return ValidationResult(
                is_valid=False,
                message=f"Shell script validation failed ({message})",
                details=details,
            )

        details["info"] = "shellcheck is not installed, skipping advanced validation"

        return ValidationResult(
            is_valid=True,
            message="Shell script validation passed",
            details=details,
        )


BaseValidator.register_validator("sh", ShellScriptValidator)
BaseValidator.register_validator("bash", ShellScriptValidator)
BaseValidator.register_validator("zsh", ShellScriptValidator)
BaseValidator.register_validator("ksh", ShellScriptValidator)
BaseValidator.register_validator("csh", ShellScriptValidator)
BaseValidator.register_validator("fish", ShellScriptValidator)
