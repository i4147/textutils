from __future__ import annotations

import os
from pathlib import Path

import pathspec

from symtext.config import ProjectConfig, Settings
from symtext.parser.parser import SUPPORTED_LANGUAGES, detect_language


def _load_gitignore_patterns(repo_path: Path) -> list[str]:
    patterns: list[str] = []

    for dirpath, _dirnames, filenames in os.walk(repo_path, followlinks=False):
        if ".gitignore" not in filenames:
            continue
        gitignore_path = Path(dirpath) / ".gitignore"
        try:
            lines = gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        rel_dir = Path(dirpath).resolve().relative_to(repo_path.resolve())
        is_root = rel_dir == Path(".")

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if is_root:
                patterns.append(stripped)
            else:
                patterns.append((rel_dir / stripped).as_posix())

    return patterns


class PathFilter:
    def __init__(
        self,
        repo_path: Path,
        settings: Settings,
        project_config: ProjectConfig | None,
        *,
        cli_includes: list[str] | None = None,
        cli_excludes: list[str] | None = None,
    ) -> None:
        self._repo_path = repo_path.resolve()
        self._max_file_size_kb = settings.max_file_size_kb

        cfg_includes: list[str] = list(project_config.include) if project_config else []
        cfg_excludes: list[str] = list(project_config.exclude) if project_config else []
        respect_gitignore = project_config.respect_gitignore if project_config else True

        raw_includes = cfg_includes
        if cli_includes:
            raw_includes.extend(cli_includes)
        self._include_paths = [Path(p) for p in raw_includes] if raw_includes else []

        raw_excludes: list[str] = []
        if respect_gitignore:
            raw_excludes.extend(_load_gitignore_patterns(self._repo_path))
        raw_excludes.extend(cfg_excludes)
        if cli_excludes:
            raw_excludes.extend(cli_excludes)
        self._exclude_spec: pathspec.PathSpec | None = (
            pathspec.PathSpec.from_lines("gitignore", raw_excludes) if raw_excludes else None
        )

    def accepts(self, path: Path) -> bool:
        try:
            rel = path.resolve().relative_to(self._repo_path)
        except ValueError:
            return False

        rel_str = rel.as_posix()

        if self._include_paths and not any(self._matches_include(rel, inc) for inc in self._include_paths):
            return False

        if self._exclude_spec and self._exclude_spec.match_file(rel_str):
            return False

        lang = detect_language(path)
        if lang is None or lang not in SUPPORTED_LANGUAGES:
            return False

        try:
            if path.stat().st_size / 1024 > self._max_file_size_kb:
                return False
        except OSError:
            return False

        return True

    def prunes_directory(self, rel_dir: str) -> bool:
        if not self._exclude_spec:
            return False
        return self._exclude_spec.match_file(rel_dir.rstrip("/") + "/")

    @staticmethod
    def _matches_include(rel: Path, include: Path) -> bool:
        try:
            rel.relative_to(include)
            return True
        except ValueError:
            return False
