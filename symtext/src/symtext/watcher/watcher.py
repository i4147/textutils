from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from watchfiles import Change, awatch

from symtext.db.graphdb import GraphDB
from symtext.graph.builder import (
    clear_file,
    index_file,
    relpath_for_db,
    resolve_cross_references,
    streaming_batch_index,
)
from symtext.parser.parser import parse_file

if TYPE_CHECKING:
    from symtext.config import Settings
    from symtext.filter import PathFilter


DbSwapHook = Callable[["GraphDB"], None]


@contextlib.asynccontextmanager
async def _maybe_lock(lock: asyncio.Lock | None) -> AsyncIterator[None]:
    if lock is None:
        yield
        return
    async with lock:
        yield


class FileWatcher:
    def __init__(
        self,
        db: GraphDB,
        settings: Settings,
        path_filter: PathFilter,
        *,
        on_db_swap: DbSwapHook | None = None,
        swap_lock: asyncio.Lock | None = None,
    ) -> None:
        self._db = db
        self._settings = settings
        self._path_filter = path_filter
        self._watched: dict[str, asyncio.Task[None]] = {}
        self._on_db_swap = on_db_swap
        self._swap_lock = swap_lock

    async def watch(self, repo_path: Path) -> None:
        repo_str = str(repo_path.resolve())
        if repo_str in self._watched:
            logger.warning("Already watching {}", repo_str)
            return

        task = asyncio.current_task()
        if task:
            self._watched[repo_str] = task

        logger.info("Watching {} for changes", repo_str)
        try:
            async for changes in awatch(
                repo_str,
                debounce=self._settings.debounce_ms,
                recursive=True,
                step=100,
            ):
                await self._process_batch(repo_path, changes)
        except asyncio.CancelledError:
            logger.info("Stopped watching {}", repo_str)
        finally:
            self._watched.pop(repo_str, None)

    async def _process_batch(self, repo_path: Path, changes: set[tuple[Change, str]]) -> None:
        if len(changes) >= self._settings.watcher_storm_threshold:
            logger.info(
                "Watcher storm ({} changes ≥ {}); triggering full reindex",
                len(changes),
                self._settings.watcher_storm_threshold,
            )
            await self._reindex_all(repo_path)
            return

        batch_results = []
        project_root = repo_path.resolve()

        with self._db.mutating_session():
            for change_type, raw_path in changes:
                path = Path(raw_path)
                rel_path = relpath_for_db(path, project_root)
                if rel_path is None:
                    logger.debug("Skipping out-of-tree change: {}", path)
                    continue

                if change_type == Change.deleted:
                    logger.debug("Deleted: {}", path)
                    clear_file(self._db, rel_path)
                    continue

                if not self._path_filter.accepts(path):
                    continue

                if change_type in (Change.added, Change.modified):
                    result = parse_file(path, settings=self._settings)
                    if result:
                        existing = self._db.get_node("File", f"File:{rel_path}")
                        if existing and existing.get("content_hash") == result.content_hash:
                            logger.debug("Unchanged (hash match): {}", path)
                            continue
                        logger.debug("Changed: {}", path)
                        clear_file(self._db, rel_path)
                        index_file(self._db, result, project_root=project_root)
                        batch_results.append(result)

            if batch_results:
                resolve_cross_references(self._db, batch_results, project_root=project_root)

    async def _reindex_all(self, repo_path: Path) -> None:
        import os
        import tempfile

        project_root = repo_path.resolve()
        path_filter = self._path_filter

        def _walk_and_parse() -> Any:
            for dirpath, dirnames, filenames in os.walk(project_root, topdown=True, followlinks=False):
                rel = Path(dirpath).relative_to(project_root).as_posix()
                dirnames[:] = [
                    d for d in dirnames if not path_filter.prunes_directory(d if rel == "." else f"{rel}/{d}")
                ]
                for fname in filenames:
                    p = Path(dirpath) / fname
                    if path_filter.accepts(p):
                        yield parse_file(p, settings=self._settings)

        def _rebuild(tmp_db_path: Path) -> int:
            fresh = GraphDB(tmp_db_path)
            fresh.create_indexes()
            try:
                return streaming_batch_index(
                    fresh,
                    _walk_and_parse(),
                    project_root=project_root,
                    batch_size=self._settings.index_batch_size,
                    batch_max_bytes=self._settings.index_batch_max_bytes,
                )
            finally:
                fresh.close()

        live_path: Path | None = getattr(self._db, "_path", None)
        if live_path is None:
            logger.warning("Storm reindex requested but live DB is in-memory; skipping")
            return

        with tempfile.TemporaryDirectory(prefix="symtext_storm_") as tmp_dir:
            tmp_db_path = Path(tmp_dir) / "index.db"
            indexed = await asyncio.to_thread(_rebuild, tmp_db_path)
            async with _maybe_lock(self._swap_lock):
                swap_src = GraphDB(tmp_db_path)
                try:
                    swap_src.atomic_swap(live_path)
                finally:
                    swap_src.close()

                old_db = self._db
                self._db = GraphDB(live_path)
                old_db.close()
                if self._on_db_swap is not None:
                    self._on_db_swap(self._db)
        logger.info("Storm reindex complete: {} files", indexed)
