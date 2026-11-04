from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from pathlib import Path

from loguru import logger

from symtext.config import Settings
from symtext.db.graphdb import GraphDB
from symtext.graph.builder import (
    clear_file,
    index_file,
    relpath_for_db,
    resolve_cross_references,
)
from symtext.parser.parser import parse_bytes

ProgressCallback = Callable[[int, int], None]


def stale_check_sweep(
    db: GraphDB,
    project_root: Path,
    settings: Settings,
    files: Iterable[Path],
    *,
    on_progress: ProgressCallback | None = None,
) -> tuple[int, int, int]:
    project_root = project_root.resolve()
    current_paths: dict[str, Path] = {}
    for p in files:
        rel = relpath_for_db(p, project_root)
        if rel is None:
            continue
        current_paths[rel] = p

    indexed_rows = db.find_nodes("File")
    indexed: dict[str, str] = {row["path"]: row.get("content_hash", "") for row in indexed_rows}

    changed_results = []
    reindexed = 0
    added = 0
    deleted = 0
    total = len(current_paths)
    max_bytes = int(settings.max_file_size_kb) * 1024

    with db.mutating_session():
        for i, (rel, abs_path) in enumerate(current_paths.items(), start=1):
            if on_progress is not None:
                on_progress(i, total)

            try:
                size = abs_path.stat().st_size
            except OSError:
                continue
            if size > max_bytes:
                if rel in indexed:
                    clear_file(db, rel)
                continue

            try:
                source = abs_path.read_bytes()
            except OSError:
                continue

            new_hash = hashlib.sha256(source).hexdigest()
            old_hash = indexed.get(rel)

            if rel in indexed and old_hash == new_hash:
                continue

            result = parse_bytes(abs_path, source)
            if result is None:
                if rel in indexed:
                    clear_file(db, rel)
                continue

            index_file(db, result, project_root=project_root)
            changed_results.append(result)
            if rel in indexed:
                reindexed += 1
            else:
                added += 1

        for rel in indexed.keys() - current_paths.keys():
            clear_file(db, rel)
            deleted += 1

        if changed_results:
            resolve_cross_references(db, changed_results, project_root=project_root)

    if reindexed or added or deleted:
        logger.info(
            "Stale-check: {} reindexed, {} added, {} deleted",
            reindexed,
            added,
            deleted,
        )
    return reindexed, added, deleted
