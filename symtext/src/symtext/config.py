from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import tomli_w
from pydantic_settings import BaseSettings

from symtext.storage import ProjectStorage, base_dir

__all__ = [
    "DEFAULT_PROJECT_CONFIG_CONTENT",
    "ProjectConfig",
    "ResolvedSettings",
    "Settings",
    "apply_project_settings",
    "load_project_config",
    "load_user_global_config",
    "read_config_file",
    "resolve_settings",
    "user_global_config_path",
    "write_config_file",
]


class Settings(BaseSettings):
    model_config = {"env_prefix": "SYMTEXT_"}

    debounce_ms: int = 500
    log_level: str = "INFO"
    max_file_size_kb: int = 512

    process_priority: Literal["low", "normal"] = "low"
    max_files: int = 50_000
    index_batch_size: int = 500
    index_batch_max_bytes: int = 100 * 1024 * 1024
    watcher_storm_threshold: int = 1000
    max_walk_depth: int = 20


DEFAULT_PROJECT_CONFIG_CONTENT = """\
# symtext per-project configuration
# Location: ~/.symtext/projects/<hash>/config.toml

[paths]
# include: only files under these directories are scanned (empty = scan everything)
# exclude: files matching these patterns are always skipped
# Excludes take precedence over includes. Patterns use gitignore syntax.
include = []
exclude = [".*", "node_modules/", "__pycache__/", "venv/", ".venv/"]
# respect_gitignore: read .gitignore files and skip matching paths (default: true)
# respect_gitignore = true

[settings]
# Any field on Settings (see config.py) can be overridden here. Examples:
# max_file_size_kb = 512
# debounce_ms = 500
# log_level = "INFO"
#
# Resource guardrails (DESIGN §8):
# process_priority = "low"   # or "normal"
# max_files = 50000
# index_batch_size = 500
# index_batch_max_bytes = 104857600
# watcher_storm_threshold = 1000
# max_walk_depth = 20
"""


@dataclass
class ProjectConfig:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    respect_gitignore: bool = True
    settings_overrides: dict[str, Any] = field(default_factory=dict)


def user_global_config_path() -> Path:
    return base_dir() / "config.toml"


def read_config_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def write_config_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        tomli_w.dump(data, f)
    os.replace(tmp, path)


def _parse_project_config(data: dict[str, Any]) -> ProjectConfig:
    paths = data.get("paths", {})
    settings_overrides = data.get("settings", {}) or {}
    return ProjectConfig(
        include=list(paths.get("include", [])),
        exclude=list(paths.get("exclude", [])),
        respect_gitignore=paths.get("respect_gitignore", True),
        settings_overrides=dict(settings_overrides),
    )


def load_project_config(project_root: Path) -> ProjectConfig:
    storage = ProjectStorage(project_root)
    data = read_config_file(storage.config_path)
    return _parse_project_config(data)


def load_user_global_config() -> ProjectConfig:
    data = read_config_file(user_global_config_path())
    return _parse_project_config(data)


class SettingsSource(StrEnum):
    DEFAULT = "default"
    USER_GLOBAL = "user-global"
    PROJECT = "per-project"
    ENV = "env"
    CLI = "cli"


@dataclass
class ResolvedSettings:
    settings: Settings
    sources: dict[str, SettingsSource] = field(default_factory=dict)


def resolve_settings(
    project_root: Path | None = None,
    *,
    cli_overrides: dict[str, Any] | None = None,
) -> ResolvedSettings:
    env_aware = Settings()
    fields = Settings.model_fields

    sources: dict[str, SettingsSource] = {}
    for field_name in fields:
        env_key = f"SYMTEXT_{field_name.upper()}"
        sources[field_name] = SettingsSource.ENV if env_key in os.environ else SettingsSource.DEFAULT

    merged: dict[str, Any] = {}

    def _apply(layer: dict[str, Any], source_name: SettingsSource) -> None:
        for key, value in layer.items():
            if key not in fields:
                continue
            if f"SYMTEXT_{key.upper()}" in os.environ:
                continue
            merged[key] = value
            sources[key] = source_name

    _apply(load_user_global_config().settings_overrides, SettingsSource.USER_GLOBAL)
    if project_root is not None:
        _apply(load_project_config(project_root).settings_overrides, SettingsSource.PROJECT)

    settings = env_aware.model_copy(update=merged) if merged else env_aware

    if cli_overrides:
        for key, value in cli_overrides.items():
            if key in fields:
                settings = settings.model_copy(update={key: value})
                sources[key] = SettingsSource.CLI

    return ResolvedSettings(settings=settings, sources=sources)


def apply_project_settings(settings: Settings, project_config: ProjectConfig) -> Settings:
    if not project_config.settings_overrides:
        return settings
    overrides = {k: v for k, v in project_config.settings_overrides.items() if k in Settings.model_fields}
    if not overrides:
        return settings
    return settings.model_copy(update=overrides)
