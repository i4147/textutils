import csv
import json
import sys
from pathlib import Path

from ...generators import register_generator
from .markdown_generator import MarkdownGenerator
from .python_generator import PythonFileGenerator
from .sh_generator import ShGenerator

print(f"Loading text generator from {__file__}", file=sys.stderr)


@register_generator(["txt", "md", "html", "css", "js", "py", "json", "csv"])
def generate_text_file(content: str, output_path: Path, **kwargs) -> Path:
    print(f"Generating text file: {output_path}", file=sys.stderr)
    if output_path.suffix.lower() in [".md", ".markdown"]:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ext = output_path.suffix.lower()[1:]

    if ext == "json":
        try:
            json_data = json.loads(content)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
            return output_path
        except json.JSONDecodeError:
            pass
    elif ext == "csv":
        try:
            rows = [line.split(",") for line in content.split("\n") if line.strip()]
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            return output_path
        except Exception:
            pass
    elif ext == "py":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# -*- coding: utf-8 -*-\n\n")
            f.write("def main():\n")
            escaped_content = content.replace('"""', '\\"\\"\\"')
            f.write(f'    print("""{escaped_content}""")\n\n')
            f.write('if __name__ == "__main__":\n')
            f.write("    main()\n")
        output_path.chmod(0o755)
        return output_path

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


__all__ = [
    "PythonFileGenerator",
    "MarkdownGenerator",
    "ShGenerator",
    "generate_text_file",
]
