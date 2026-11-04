from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from symtext import registry
from symtext.lock import read_holder, try_acquire
from symtext.storage import ProjectStorage, base_dir


@dataclass
class OrphanCandidate:
    project_hash: str
    hash_dir: str
    project_path: str | None
    reason: str
    locked: bool
    lock_holder: str | None = None
    size_bytes: int = 0

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def _hash_dir_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def _is_locked(storage: ProjectStorage) -> tuple[bool, str | None]:
    for path in (storage.watcher_lock_path, storage.index_lock_path):
        if not path.exists():
            continue
        handle = try_acquire(path, tag="gc-probe")
        if handle is None:
            return True, read_holder(path) or "(unknown)"
        handle.release()
    return False, None


def find_orphans() -> list[OrphanCandidate]:
    projects_dir = base_dir() / "projects"
    if not projects_dir.is_dir():
        return []

    out: list[OrphanCandidate] = []
    for child in projects_dir.iterdir():
        if not child.is_dir():
            continue
        record_path = child / "project.json"

        project_path: str | None = None
        reason: str
        if not record_path.is_file():
            reason = "no project.json"
        else:
            try:
                with open(record_path, encoding="utf-8") as f:
                    project_path = json.load(f).get("project_path")
            except (OSError, json.JSONDecodeError):
                reason = "unreadable project.json"
                project_path = None
            else:
                if not project_path:
                    reason = "project.json missing project_path"
                elif Path(project_path).exists():
                    continue
                else:
                    reason = "project_path no longer exists"

        storage = ProjectStorage.from_hash(
            child.name,
            Path(project_path) if project_path else child,
        )
        locked, holder = _is_locked(storage)

        out.append(
            OrphanCandidate(
                project_hash=child.name,
                hash_dir=str(child),
                project_path=project_path,
                reason=reason,
                locked=locked,
                lock_holder=holder,
                size_bytes=_hash_dir_size(child),
            )
        )
    return out


def collect(*, force: bool = False) -> tuple[list[OrphanCandidate], list[OrphanCandidate]]:
    candidates = find_orphans()
    removed: list[OrphanCandidate] = []
    skipped: list[OrphanCandidate] = []

    for cand in candidates:
        if cand.locked:
            skipped.append(cand)
            continue
        if not force:
            skipped.append(cand)
            continue
        try:
            shutil.rmtree(cand.hash_dir)
        except OSError as exc:
            logger.warning("Failed to remove {}: {}", cand.hash_dir, exc)
            skipped.append(cand)
            continue
        registry.remove(cand.project_hash)
        removed.append(cand)

    return removed, skipped
