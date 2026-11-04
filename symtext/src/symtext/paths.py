from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path


VCS_MARKERS: frozenset[str] = frozenset({".git", ".hg", ".jj", ".svn", ".bzr", "CVS", "_darcs", ".fossil"})

BUILD_MARKERS: frozenset[str] = frozenset({
    "pyproject.toml",
    "setup.py",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "mix.exs",
    "Package.swift",
    "composer.json",
    "pubspec.yaml",
    "CMakeLists.txt",
    "Makefile",
})

STRONG_AI_MARKERS: frozenset[str] = frozenset({
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    ".cursorrules",
    ".windsurfrules",
    ".continuerules",
    ".clinerules",
    ".aider.conf.yml",
})

STRONG_AI_NESTED: tuple[tuple[str, ...], ...] = ((".github", "copilot-instructions.md"),)


def canonical_project_path(path: Path | str) -> Path:
    resolved = Path(path).resolve(strict=True)
    try:
        str(resolved).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"Project path is not UTF-8 encodable: {path!r}") from exc
    return resolved


def project_hash(path: Path | str) -> str:
    canonical = canonical_project_path(path)
    digest = hashlib.sha256(str(canonical).encode("utf-8")).hexdigest()
    return digest[:12]


def _windows_refused_dirs() -> set[Path]:
    keys = (
        "WINDIR",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "APPDATA",
        "LOCALAPPDATA",
        "TEMP",
        "TMP",
    )
    refused: set[Path] = set()
    for key in keys:
        val = os.environ.get(key)
        if val:
            try:
                refused.add(Path(val).resolve(strict=False))
            except OSError:
                continue
    return refused


def _posix_refused_dirs() -> set[Path]:
    refused: set[Path] = set()
    for raw in ("/tmp", "/var", "/etc", "/usr", "/opt", "/root", "/srv"):
        candidate = Path(raw)
        refused.add(candidate)
        try:
            refused.add(candidate.resolve(strict=False))
        except OSError:
            continue
    return refused


def refused_directories() -> set[Path]:
    refused: set[Path] = {Path.home().resolve(strict=False)}

    if sys.platform.startswith("win"):
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            root = Path(f"{letter}:\\")
            if root.exists():
                refused.add(root)
        refused.update(_windows_refused_dirs())
    else:
        refused.add(Path("/"))
        refused.update(_posix_refused_dirs())

    return refused


def is_refused_directory(path: Path | str) -> bool:
    try:
        canonical = Path(path).resolve(strict=False)
    except OSError:
        return False
    return canonical in refused_directories()


def _has_vcs_marker(directory: Path) -> bool:
    for name in VCS_MARKERS:
        candidate = directory / name
        if candidate.is_dir() or candidate.is_file():
            return True
    return False


def _has_strong_marker(directory: Path) -> bool:
    for name in BUILD_MARKERS:
        if (directory / name).is_file():
            return True
    for name in STRONG_AI_MARKERS:
        if (directory / name).is_file():
            return True
    return any(directory.joinpath(*parts).is_file() for parts in STRONG_AI_NESTED)


SYMTEXT_ROOT_MARKER = ".symtext-root"


def _has_explicit_root_marker(directory: Path) -> bool:
    marker = directory / SYMTEXT_ROOT_MARKER
    return marker.is_file() or marker.is_dir()


def find_project_root(cwd: Path | str) -> Path:
    start = canonical_project_path(cwd)
    home = Path.home().resolve(strict=False)
    refused = refused_directories()

    highest_strong: Path | None = None

    current = start
    while True:
        if current in refused:
            break
        if _has_explicit_root_marker(current):
            return current
        if _has_vcs_marker(current):
            return current
        if _has_strong_marker(current):
            highest_strong = current

        if current == home or current.parent == current:
            break
        current = current.parent

    return highest_strong if highest_strong is not None else start
