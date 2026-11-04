from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from symtext.db.graphdb import GraphDB
from symtext.filter import PathFilter
from symtext.lock import read_holder, try_acquire
from symtext.mcp.handlers import set_project_root
from symtext.mcp.server import serve
from symtext.mcp.state import ServerContext, ServerState
from symtext.watcher.watcher import FileWatcher

if TYPE_CHECKING:
    from symtext.config import ProjectConfig, Settings
    from symtext.storage import ProjectStorage


__all__ = ["McpRuntime", "run_mcp", "run_refused_mcp"]


IndexFn = Callable[..., None]
CollectFilesFn = Callable[[Path, "PathFilter", "Settings | None"], list[Path]]


@dataclass
class McpRuntime:
    db: GraphDB | None = None
    watch_lock: Any | None = None
    watcher_task: asyncio.Task[None] | None = None
    swap_lock: asyncio.Lock | None = None


class _DbProxy:
    def __init__(self, runtime: McpRuntime) -> None:
        self._runtime = runtime

    def __getattr__(self, name: str) -> Any:
        db = self._runtime.db
        if db is None:
            raise RuntimeError(
                "GraphDB not yet available — tool dispatch should have been gated by ServerContext.is_ready()."
            )
        return getattr(db, name)


def _start_watcher_task(
    *,
    runtime: McpRuntime,
    db: GraphDB,
    project_root: Path,
    settings: Settings,
    project_config: ProjectConfig | None,
) -> None:
    path_filter = PathFilter(project_root, settings, project_config)

    def _on_db_swap(new_db: GraphDB) -> None:
        runtime.db = new_db

    watcher = FileWatcher(
        db,
        settings,
        path_filter,
        on_db_swap=_on_db_swap,
        swap_lock=runtime.swap_lock,
    )
    runtime.watcher_task = asyncio.create_task(watcher.watch(project_root))


def _try_promote_to_watcher(
    *,
    ctx: ServerContext,
    runtime: McpRuntime,
    storage: ProjectStorage,
    project_root: Path,
    settings: Settings,
    project_config: ProjectConfig | None,
) -> None:
    if ctx.promotion_done or not ctx.is_reader_only:
        return
    lock = try_acquire(storage.watcher_lock_path, tag="watcher")
    if lock is None:
        return
    runtime.watch_lock = lock
    db = runtime.db
    if db is None:
        lock.release()
        runtime.watch_lock = None
        return
    _start_watcher_task(
        runtime=runtime,
        db=db,
        project_root=project_root,
        settings=settings,
        project_config=project_config,
    )
    ctx.promotion_done = True
    ctx.is_reader_only = False


async def _drive_startup(
    *,
    ctx: ServerContext,
    runtime: McpRuntime,
    project_root: Path,
    storage: ProjectStorage,
    settings: Settings,
    project_config: ProjectConfig | None,
    watch: bool,
    run_index: IndexFn,
    collect_files: CollectFilesFn,
) -> None:
    from symtext.db.graphdb import DB_SCHEMA_VERSION
    from symtext.graph.stale import stale_check_sweep

    try:
        if not storage.db_path.exists():
            ctx.set_state(ServerState.INITIAL_INDEX)
            await asyncio.to_thread(
                run_index,
                project_root,
                storage,
                settings,
                project_config,
                None,
                None,
                to_stderr=True,
            )
        else:
            probe = GraphDB(storage.db_path)
            try:
                recorded = probe.schema_version()
            finally:
                probe.close()
            if recorded != DB_SCHEMA_VERSION:
                logger.info(
                    "Schema drift: DB has v{}, code expects v{} — reindexing",
                    recorded,
                    DB_SCHEMA_VERSION,
                )
                ctx.set_state(ServerState.INDEXING_REINDEX)
                await asyncio.to_thread(run_index, project_root, storage, settings, project_config)

        runtime.db = GraphDB(storage.db_path)

        ctx.set_state(ServerState.STALE_CHECKING)
        path_filter = PathFilter(project_root, settings, project_config)
        files = collect_files(project_root, path_filter, settings)
        ctx.update_progress(0, len(files))
        await asyncio.to_thread(
            stale_check_sweep,
            runtime.db,
            project_root,
            settings,
            files,
            on_progress=ctx.update_progress,
        )

        if watch:
            lock = try_acquire(storage.watcher_lock_path, tag="watcher")
            if lock is not None:
                runtime.watch_lock = lock
                _start_watcher_task(
                    runtime=runtime,
                    db=runtime.db,
                    project_root=project_root,
                    settings=settings,
                    project_config=project_config,
                )
                logger.info("File watcher enabled for {}", project_root)
            else:
                holder = read_holder(storage.watcher_lock_path) or "another session"
                logger.info("Watcher lock held by {}; this MCP session is read-only.", holder)
                ctx.is_reader_only = True

        ctx.set_state(ServerState.READY)
        logger.info("symtext MCP server READY for {}", project_root)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.opt(exception=True).error("Startup failed: {}", exc)
        ctx.set_state(ServerState.ERROR, error_message=str(exc))


async def run_refused_mcp(cwd: Path) -> None:
    ctx = ServerContext()
    ctx.set_state(
        ServerState.ERROR,
        error_message=(
            f"{cwd} is a refused directory (home / system / temp). symtext only operates inside project directories."
        ),
    )
    await serve(db=None, ctx=ctx)


async def run_mcp(
    *,
    project_root: Path,
    storage: ProjectStorage,
    settings: Settings,
    project_config: ProjectConfig | None,
    watch: bool,
    run_index: IndexFn,
    collect_files: CollectFilesFn,
) -> None:
    set_project_root(project_root)
    ctx = ServerContext()
    runtime = McpRuntime(swap_lock=asyncio.Lock())

    async def _startup() -> None:
        await _drive_startup(
            ctx=ctx,
            runtime=runtime,
            project_root=project_root,
            storage=storage,
            settings=settings,
            project_config=project_config,
            watch=watch,
            run_index=run_index,
            collect_files=collect_files,
        )

    startup_task = asyncio.create_task(_startup())

    def _promotion_hook() -> None:
        _try_promote_to_watcher(
            ctx=ctx,
            runtime=runtime,
            storage=storage,
            project_root=project_root,
            settings=settings,
            project_config=project_config,
        )

    db_proxy = _DbProxy(runtime)

    try:
        await serve(
            db_proxy,
            ctx=ctx,
            promotion_hook=_promotion_hook,
            swap_lock=runtime.swap_lock,
        )
    except KeyboardInterrupt:
        pass
    finally:
        startup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await startup_task
        if runtime.watcher_task is not None:
            runtime.watcher_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await runtime.watcher_task
        if runtime.db is not None:
            runtime.db.close()
        if runtime.watch_lock is not None:
            runtime.watch_lock.release()
