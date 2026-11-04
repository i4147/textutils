from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from symtext import __version__
from symtext.paths import project_hash

PROJECT_JSON_SCHEMA_VERSION = 1

_METADATA_PRIORITY: tuple[tuple[str, str], ...] = (
    ("pyproject.toml", "python"),
    ("package.json", "javascript"),
    ("Cargo.toml", "rust"),
    ("go.mod", "go"),
    ("composer.json", "php"),
    ("pubspec.yaml", "dart"),
)


def _utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base_dir() -> Path:
    override = os.environ.get("SYMTEXT_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".symtext"


@dataclass
class ProjectMetadata:
    name: str
    description: str = ""
    primary_language: str = ""


def extract_project_metadata(project_root: Path) -> ProjectMetadata:
    for filename, language in _METADATA_PRIORITY:
        path = project_root / filename
        if not path.is_file():
            continue
        try:
            meta = _parse_manifest(path, filename)
        except (OSError, ValueError, tomllib.TOMLDecodeError, json.JSONDecodeError):
            continue
        if meta is None:
            continue
        return ProjectMetadata(
            name=meta.get("name") or project_root.name,
            description=meta.get("description", ""),
            primary_language=language,
        )
    return ProjectMetadata(name=project_root.name)


def _parse_manifest(path: Path, filename: str) -> dict[str, str] | None:
    if filename == "pyproject.toml":
        with open(path, "rb") as f:
            data = tomllib.load(f)
        project = data.get("project", {})
        name = project.get("name") or data.get("tool", {}).get("poetry", {}).get("name", "")
        desc = project.get("description") or data.get("tool", {}).get("poetry", {}).get("description", "")
        return {"name": name, "description": desc}
    if filename == "package.json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {"name": data.get("name", ""), "description": data.get("description", "")}
    if filename == "Cargo.toml":
        with open(path, "rb") as f:
            data = tomllib.load(f)
        package = data.get("package", {})
        return {"name": package.get("name", ""), "description": package.get("description", "")}
    if filename == "go.mod":
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("module "):
                    return {"name": line.split(None, 1)[1].rsplit("/", 1)[-1], "description": ""}
        return None
    if filename == "composer.json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {"name": data.get("name", ""), "description": data.get("description", "")}
    if filename == "pubspec.yaml":
        name = ""
        description = ""
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
        return {"name": name, "description": description}
    return None


@dataclass
class ProjectRecord:
    schema_version: int = PROJECT_JSON_SCHEMA_VERSION
    project_hash: str = ""
    project_path: str = ""
    project_name: str = ""
    project_description: str = ""
    primary_language: str = ""
    created_at: str = ""
    last_opened_at: str = ""
    first_indexed_with: str = ""
    current_symtext_version: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_hash": self.project_hash,
            "project_path": self.project_path,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "primary_language": self.primary_language,
            "created_at": self.created_at,
            "last_opened_at": self.last_opened_at,
            "first_indexed_with": self.first_indexed_with,
            "current_symtext_version": self.current_symtext_version,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ProjectRecord:
        return cls(
            schema_version=data.get("schema_version", PROJECT_JSON_SCHEMA_VERSION),
            project_hash=data.get("project_hash", ""),
            project_path=data.get("project_path", ""),
            project_name=data.get("project_name", ""),
            project_description=data.get("project_description", ""),
            primary_language=data.get("primary_language", ""),
            created_at=data.get("created_at", ""),
            last_opened_at=data.get("last_opened_at", ""),
            first_indexed_with=data.get("first_indexed_with", ""),
            current_symtext_version=data.get("current_symtext_version", ""),
        )


class ProjectStorage:
    def __init__(self, project_root: Path) -> None:
        self.project_root: Path = project_root.resolve()
        self.project_hash: str = project_hash(self.project_root)

    @classmethod
    def from_hash(cls, project_hash: str, project_root: Path) -> ProjectStorage:
        obj = cls.__new__(cls)
        obj.project_root = project_root
        obj.project_hash = project_hash
        return obj

    @property
    def project_dir(self) -> Path:
        return base_dir() / "projects" / self.project_hash

    @property
    def db_path(self) -> Path:
        return self.project_dir / "index.db"

    @property
    def project_json_path(self) -> Path:
        return self.project_dir / "project.json"

    @property
    def log_path(self) -> Path:
        return self.project_dir / "symtext.log"

    @property
    def watcher_lock_path(self) -> Path:
        return self.project_dir / "lock"

    @property
    def index_lock_path(self) -> Path:
        return self.project_dir / "index.lock"

    @property
    def config_path(self) -> Path:
        return self.project_dir / "config.toml"

    def ensure_initialized(self) -> None:
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def load_record(self) -> ProjectRecord | None:
        if not self.project_json_path.is_file():
            return None
        with open(self.project_json_path, encoding="utf-8") as f:
            data = json.load(f)
        record = ProjectRecord.from_json(data)
        if record.project_hash and record.project_hash != self.project_hash:
            raise ValueError(
                f"project.json hash mismatch in {self.project_dir}: "
                f"file says {record.project_hash!r}, dir is {self.project_hash!r}"
            )
        return record

    def save_record(self, record: ProjectRecord) -> None:
        self.ensure_initialized()
        tmp = self.project_json_path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(record.to_json(), f, indent=2)
            f.write("\n")
        os.replace(tmp, self.project_json_path)

    def touch(self, metadata: ProjectMetadata | None = None) -> ProjectRecord:
        now = _utcnow_iso()
        existing = self.load_record()
        if existing is None:
            record = ProjectRecord(
                project_hash=self.project_hash,
                project_path=str(self.project_root),
                project_name=metadata.name if metadata else self.project_root.name,
                project_description=metadata.description if metadata else "",
                primary_language=metadata.primary_language if metadata else "",
                created_at=now,
                last_opened_at=now,
                first_indexed_with=__version__,
                current_symtext_version=__version__,
            )
        else:
            record = existing
            record.project_path = str(self.project_root)
            record.last_opened_at = now
            record.current_symtext_version = __version__
            if metadata is not None:
                record.project_name = metadata.name or record.project_name
                record.project_description = metadata.description or record.project_description
                record.primary_language = metadata.primary_language or record.primary_language
        self.save_record(record)
        return record


def storage_for(project_root: Path) -> ProjectStorage:
    return ProjectStorage(project_root)
