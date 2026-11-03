from __future__ import annotations
from typing import List


def read_text(path: str, encoding: str = "utf-8") -> str:
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except OSError as exc:
        raise RuntimeError(f"Failed to read file: {path}") from exc


def write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    try:
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
    except OSError as exc:
        raise RuntimeError(f"Failed to write file: {path}") from exc


def append_text(path: str, content: str, encoding: str = "utf-8") -> None:
    try:
        with open(path, "a", encoding=encoding) as f:
            f.write(content)
    except OSError as exc:
        raise RuntimeError(f"Failed to append file: {path}") from exc


def read_lines(path: str, encoding: str = "utf-8") -> list[str]:
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.readlines()
    except OSError as exc:
        raise RuntimeError(f"Failed to read file lines: {path}") from exc


def write_lines(path: str, lines: list[str], encoding: str = "utf-8") -> None:
    try:
        with open(path, "w", encoding=encoding) as f:
            f.writelines(lines)
    except OSError as exc:
        raise RuntimeError(f"Failed to write lines: {path}") from exc
