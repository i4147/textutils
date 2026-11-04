import os
import stat
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ...generators import register_generator
from ...utils.file_utils import ensure_directory
from ...validators.base import ValidationResult
from ..base import BaseGenerator


class ShGenerator(BaseGenerator):
    @classmethod
    def generate(
        cls,
        content: str,
        output_path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        shebang = kwargs.get("shebang", "#!/bin/bash")
        description = kwargs.get("description", "A generated shell script")
        encoding = kwargs.get("encoding", "utf-8")

        escaped_content = (
            content
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("`", "\\`")
            .replace("$", "\\$")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )

        lines = []

        lines.append(f"{shebang}")

        if description:
            lines.append("")
            lines.append("# " + "=" * 77)
            for line in description.split("\n"):
                lines.append(f"# {line}")
            lines.append("# " + "=" * 77)

        lines.append("")
        lines.append(escaped_content)

        script_content = "\n".join(lines).strip() + "\n"

        output_path.write_text(script_content, encoding=encoding)

        try:
            st = os.stat(output_path)
            os.chmod(output_path, st.st_mode | stat.S_IEXEC)
        except (OSError, AttributeError):
            pass

        return output_path

    @classmethod
    def validate(cls, file_path: Union[str, Path]) -> ValidationResult:
        from ...validators.text_validator import ShellScriptValidator

        return ShellScriptValidator.validate(file_path)


@register_generator(["sh", "bash"])
def generate_sh(content: str, output_path: Union[str, Path], **kwargs: Any) -> Path:
    return ShGenerator.generate(content, output_path, **kwargs)
