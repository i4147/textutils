from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import portalocker

from symtext.storage import ProjectRecord, ProjectStorage, _utcnow_iso, base_dir

REGISTRY_SCHEMA_VERSION = 1


def registry_path() -> Path:
    return base_dir() / "projects.json"


def registry_lock_path() -> Path:
    return base_dir() / "projects.json.lock"


@dataclass
class RegistryEntry:
    project_path: str = ""
    project_name: str = ""
    primary_language: str = ""
    created_at: str = ""
    last_opened_at: str = ""
    first_indexed_with: str = ""

    @classmethod
    def from_record(cls, record: ProjectRecord) -> RegistryEntry:
        return cls(
            project_path=record.project_path,
            project_name=record.project_name,
            primary_language=record.primary_language,
            created_at=record.created_at,
            last_opened_at=record.last_opened_at,
            first_indexed_with=record.first_indexed_with,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "primary_language": self.primary_language,
            "created_at": self.created_at,
            "last_opened_at": self.last_opened_at,
            "first_indexed_with": self.first_indexed_with,
        }


def load() -> dict[str, RegistryEntry]:
    path = registry_path()
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    projects = data.get("projects", {})
    known = {f.name for f in fields(RegistryEntry)}
    return {h: RegistryEntry(**{k: v for k, v in entry.items() if k in known}) for h, entry in projects.items()}


def _write_atomic(entries: dict[str, RegistryEntry]) -> None:
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "updated_at": _utcnow_iso(),
        "projects": {h: e.to_json() for h, e in sorted(entries.items())},
    }
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _with_lock(callback: Any) -> Any:
    lock_path = registry_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as fh:
        portalocker.lock(fh, portalocker.LOCK_EX)
        try:
            return callback()
        finally:
            portalocker.unlock(fh)


def upsert(project_hash: str, entry: RegistryEntry) -> None:

    def _do() -> None:
        entries = load()
        entries[project_hash] = entry
        _write_atomic(entries)

    _with_lock(_do)


def remove(project_hash: str) -> bool:

    def _do() -> bool:
        entries = load()
        if project_hash not in entries:
            return False
        del entries[project_hash]
        _write_atomic(entries)
        return True

    return bool(_with_lock(_do))


def rebuild() -> dict[str, RegistryEntry]:

    def _do() -> dict[str, RegistryEntry]:
        projects_dir = base_dir() / "projects"
        entries: dict[str, RegistryEntry] = {}
        if projects_dir.is_dir():
            for child in projects_dir.iterdir():
                if not child.is_dir():
                    continue
                record_path = child / "project.json"
                if not record_path.is_file():
                    continue
                try:
                    with open(record_path, encoding="utf-8") as f:
                        data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
                record = ProjectRecord.from_json(data)
                if not record.project_hash:
                    record.project_hash = child.name
                entries[record.project_hash] = RegistryEntry.from_record(record)
        _write_atomic(entries)
        return entries

    return _with_lock(_do)


def refresh_from_storage(storage: ProjectStorage) -> None:
    record = storage.load_record()
    if record is None:
        return
    upsert(storage.project_hash, RegistryEntry.from_record(record))
