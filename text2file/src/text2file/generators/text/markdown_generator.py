import textwrap
from pathlib import Path
from typing import Any, List, Optional, Union

from ...generators import register_generator
from ...utils.file_utils import ensure_directory
from ...utils.text_utils import wrap_text
from ...validators.base import ValidationResult
from ..base import BaseGenerator


class MarkdownGenerator(BaseGenerator):
    @classmethod
    def generate(
        cls,
        content: str,
        output_path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        title = kwargs.get("title", "Generated Document")
        author = kwargs.get("author")
        date = kwargs.get("date", None)
        width = int(kwargs.get("width", 80))
        add_toc = bool(kwargs.get("add_toc", False))
        add_hr = bool(kwargs.get("add_hr", True))
        encoding = kwargs.get("encoding", "utf-8")

        from datetime import datetime

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []

        lines.append(f"# {title}\n")

        if author or date:
            meta = []
            if author:
                meta.append(f"**Author:** {author}")
            if date:
                meta.append(f"**Date:** {date}")
            lines.append(" | ".join(meta) + "\n")

        if add_hr:
            lines.append("---\n")

        if add_toc:
            lines.append("## Table of Contents\n")
            lines.append("* [Introduction](#introduction)\n")
            lines.append("* [Usage](#usage)\n")
            lines.append("* [Examples](#examples)\n\n")

        wrapped_content = wrap_text(content, width=width)
        lines.append(wrapped_content)

        markdown_content = "\n".join(lines).strip() + "\n"

        output_path.write_text(markdown_content, encoding=encoding)

        return output_path

    @classmethod
    def validate(cls, file_path: Union[str, Path]) -> ValidationResult:
        from ...validators.text_validator import MarkdownValidator

        return MarkdownValidator.validate(file_path)


@register_generator(["md", "markdown"])
def generate_md(content: str, output_path: Union[str, Path], **kwargs: Any) -> Path:
    return MarkdownGenerator.generate(content, output_path, **kwargs)
