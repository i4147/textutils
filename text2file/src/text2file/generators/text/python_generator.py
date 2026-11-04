import sys
from pathlib import Path
from typing import Any, List, Optional, Union

from ...generators import register_generator
from ...utils.file_utils import ensure_directory
from ...validators.base import ValidationResult
from ..base import BaseGenerator


class PythonFileGenerator(BaseGenerator):
    @classmethod
    def generate(
        cls,
        content: str,
        output_path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        shebang = kwargs.get("shebang", "#!/usr/bin/env python3")
        docstring = kwargs.get("docstring", "A generated Python script")
        imports = kwargs.get("imports", [])
        main_guard = kwargs.get("main_guard", True)
        encoding = kwargs.get("encoding", "utf-8")

        escaped_content = (
            content
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )

        lines = []

        if shebang:
            lines.append(f"{shebang}\n")

        lines.append(f"# -*- coding: {encoding} -*-\n")

        if docstring:
            lines.append(f'"""{docstring}"""\n')

        for imp in imports:
            if isinstance(imp, str):
                lines.append(f"import {imp}")
            elif isinstance(imp, (list, tuple)) and len(imp) == 2:
                lines.append(f"from {imp[0]} import {imp[1]}")

        if imports:
            lines.append("")

        if main_guard:
            lines.append("def main():")
            content_lines = [f'    print("{escaped_content}")']
            lines.extend(content_lines)
            lines.append("")
            lines.append("")
            lines.append('if __name__ == "__main__":')
            lines.append("    main()")
        else:
            lines.append(f'print("{escaped_content}")')

        script_content = "\n".join(lines).strip() + "\n"

        output_path.write_text(script_content, encoding=encoding)

        if shebang and shebang.startswith("#!"):
            try:
                output_path.chmod(0o755)
            except (OSError, NotImplementedError):
                pass

        return output_path

    @classmethod
    def validate(cls, file_path: Union[str, Path]) -> ValidationResult:
        from ...validators.text_validator import PythonFileValidator

        return PythonFileValidator.validate(file_path)


@register_generator(["py", "python"])
def generate_py(content: str, output_path: Union[str, Path], **kwargs: Any) -> Path:
    return PythonFileGenerator.generate(content, output_path, **kwargs)
