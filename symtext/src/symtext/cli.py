from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from loguru import logger

from symtext import __version__, registry
from symtext.config import (
    ProjectConfig,
    Settings,
    apply_project_settings,
    load_project_config,
)
from symtext.db.graphdb import GraphDB
from symtext.filter import PathFilter
from symtext.graph.builder import streaming_batch_index
from symtext.lock import read_holder, try_acquire
from symtext.parser.parser import parse_file
from symtext.paths import find_project_root, is_refused_directory
from symtext.process import apply_process_priority
from symtext.storage import ProjectStorage, extract_project_metadata
from symtext.watcher.watcher import FileWatcher

app = typer.Typer(
    name="symtext",
    help="Code graph indexer and MCP server.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

from symtext.config_cli import config_app

app.add_typer(config_app, name="config")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"symtext {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    pass


def _setup_logging(settings: Settings, log_path: Path) -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(log_path), level="DEBUG", rotation="10 MB")


def _err(msg: str) -> None:
    typer.echo(typer.style(msg, fg=typer.colors.RED), err=True)


def _resolve_project(cwd: Path, *, refuse_ok: bool = False) -> tuple[Path, ProjectStorage]:
    if is_refused_directory(cwd) and not refuse_ok:
        _err(f"symtext refuses to operate in {cwd} (system/home directory). Run from inside a project.")
        raise typer.Exit(1)
    project_root = find_project_root(cwd)
    storage = ProjectStorage(project_root)
    storage.ensure_initialized()
    storage.touch(extract_project_metadata(project_root))
    registry.refresh_from_storage(storage)
    return project_root, storage


def _collect_files(
    repo_path: Path,
    path_filter: PathFilter,
    settings: Settings | None = None,
) -> list[Path]:
    import os

    resolved = repo_path.resolve()
    max_depth = settings.max_walk_depth if settings is not None else None
    max_files = settings.max_files if settings is not None else None

    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(resolved, topdown=True, followlinks=False):
        rel_dir_path = Path(dirpath).relative_to(resolved)
        rel_dir = str(rel_dir_path)
        rel_dir_posix = rel_dir_path.as_posix()
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                d
                for d in dirnames
                if not path_filter.prunes_directory(d if rel_dir_posix == "." else f"{rel_dir_posix}/{d}")
            ]
        for fname in filenames:
            p = Path(dirpath) / fname
            if path_filter.accepts(p):
                files.append(p)
                if max_files is not None and len(files) > max_files:
                    _err(
                        f"Project exceeds max_files ({max_files}); refusing to index. "
                        f"Lower the candidate set via paths.exclude or raise max_files."
                    )
                    raise typer.Exit(1)
    return files


_INDEX_WAIT_TIMEOUT_S = 600
_INDEX_POLL_INTERVAL_S = 0.5


def _wait_for_concurrent_indexer(storage: ProjectStorage, echo: Callable[[str], None]) -> bool:
    holder = read_holder(storage.index_lock_path) or "another process"
    echo(typer.style(f"Indexing in progress ({holder}); waiting…", fg=typer.colors.YELLOW))
    deadline = time.monotonic() + _INDEX_WAIT_TIMEOUT_S
    while time.monotonic() < deadline:
        if storage.db_path.exists():
            return True
        probe = try_acquire(storage.index_lock_path, tag="indexer-probe")
        if probe is not None:
            probe.release()
            return storage.db_path.exists()
        time.sleep(_INDEX_POLL_INTERVAL_S)
    _err(f"Timed out after {_INDEX_WAIT_TIMEOUT_S}s waiting for indexer.")
    raise typer.Exit(1)


def _run_index(
    repo_path: Path,
    storage: ProjectStorage,
    settings: Settings,
    project_config: ProjectConfig | None = None,
    cli_includes: list[str] | None = None,
    cli_excludes: list[str] | None = None,
    *,
    to_stderr: bool = False,
) -> None:

    def _echo(msg: str) -> None:
        typer.echo(msg, err=to_stderr)

    while True:
        lock_handle = try_acquire(storage.index_lock_path, tag="indexer")

        if lock_handle is not None:
            try:
                _do_index(
                    repo_path,
                    storage,
                    settings,
                    project_config,
                    cli_includes,
                    cli_excludes,
                    echo=_echo,
                )
            finally:
                lock_handle.release()
            return

        produced_db = _wait_for_concurrent_indexer(storage, _echo)
        if produced_db:
            _echo(typer.style("Using index produced by other process.", fg=typer.colors.GREEN))
            return
        _echo(typer.style("Indexer aborted; taking over.", fg=typer.colors.YELLOW))


def _do_index(
    repo_path: Path,
    storage: ProjectStorage,
    settings: Settings,
    project_config: ProjectConfig | None,
    cli_includes: list[str] | None,
    cli_excludes: list[str] | None,
    *,
    echo: Callable[[str], None],
) -> None:
    if project_config is None:
        project_config = load_project_config(repo_path)

    path_filter = PathFilter(repo_path, settings, project_config, cli_includes=cli_includes, cli_excludes=cli_excludes)
    files = _collect_files(repo_path, path_filter, settings)

    t0 = time.perf_counter()
    echo(typer.style(f"Indexing {len(files)} files from {repo_path}", fg=typer.colors.CYAN))

    def _parse_stream() -> Any:
        for f in files:
            yield parse_file(f, settings=settings)

    with tempfile.TemporaryDirectory(prefix="symtext_idx_") as tmp_dir:
        tmp_db_path = Path(tmp_dir) / "index.db"
        db = GraphDB(tmp_db_path)
        db.create_indexes()

        indexed = streaming_batch_index(
            db,
            _parse_stream(),
            project_root=repo_path,
            batch_size=settings.index_batch_size,
            batch_max_bytes=settings.index_batch_max_bytes,
        )
        db.init_metadata(
            symtext_version=__version__,
            project_root=str(repo_path),
            created_at=datetime.now(UTC).isoformat(),
        )
        db.atomic_swap(storage.db_path)
        db.close()

    t_total = time.perf_counter() - t0
    msg = f"Done. Indexed {indexed} files in {t_total:.1f}s → {storage.db_path}"
    echo(typer.style(msg, fg=typer.colors.GREEN))


@app.command()
def index(
    path: str = typer.Argument(..., help="Path to repository to index"),
    watch: bool = typer.Option(False, "-w", "--watch", help="Watch for changes after initial index"),
    include: Annotated[
        list[str] | None,
        typer.Option("-I", "--include", help="Include path (repeatable, extends .symtext.toml)"),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("-X", "--exclude", help="Exclude pattern (repeatable, extends .symtext.toml)"),
    ] = None,
) -> None:
    settings = Settings()
    apply_process_priority(settings.process_priority)
    repo_path = Path(path).resolve()

    if not repo_path.is_dir():
        _err(f"Error: {path} is not a directory")
        raise typer.Exit(1)

    project_root, storage = _resolve_project(repo_path)
    _setup_logging(settings, storage.log_path)

    project_config = load_project_config(project_root)
    settings = apply_project_settings(settings, project_config)
    _run_index(project_root, storage, settings, project_config, include, exclude)

    if watch:
        typer.echo(typer.style("Switching to watch mode...", fg=typer.colors.CYAN))
        _run_watch(project_root, storage, settings, project_config, include, exclude)


def _run_watch(
    repo_path: Path,
    storage: ProjectStorage,
    settings: Settings,
    project_config: ProjectConfig | None = None,
    cli_includes: list[str] | None = None,
    cli_excludes: list[str] | None = None,
    *,
    require_lock: bool = True,
) -> None:
    if project_config is None:
        project_config = load_project_config(repo_path)

    watch_lock = try_acquire(storage.watcher_lock_path, tag="watcher")
    if watch_lock is None:
        holder = read_holder(storage.watcher_lock_path) or "another process"
        if require_lock:
            _err(f"Watcher already running for this project ({holder}).")
            raise typer.Exit(1)
        logger.info("Watcher lock held by {}; running read-only.", holder)
        return

    db = GraphDB(storage.db_path)
    path_filter = PathFilter(repo_path, settings, project_config, cli_includes=cli_includes, cli_excludes=cli_excludes)
    watcher = FileWatcher(db, settings, path_filter)
    try:
        asyncio.run(watcher.watch(repo_path))
    except KeyboardInterrupt:
        typer.echo("\nStopped watching.")
    finally:
        db.close()
        watch_lock.release()


@app.command("watch")
def watch_cmd(
    path: str = typer.Argument(..., help="Path to repository to watch"),
    include: Annotated[
        list[str] | None,
        typer.Option("-I", "--include", help="Include path (repeatable, extends .symtext.toml)"),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("-X", "--exclude", help="Exclude pattern (repeatable, extends .symtext.toml)"),
    ] = None,
) -> None:
    settings = Settings()
    repo_path = Path(path).resolve()

    if not repo_path.is_dir():
        _err(f"Error: {path} is not a directory")
        raise typer.Exit(1)

    project_root, storage = _resolve_project(repo_path)
    _setup_logging(settings, storage.log_path)

    if not storage.db_path.exists():
        _err("No index found. Run `symtext index` first.")
        raise typer.Exit(1)

    typer.echo(typer.style(f"Watching {project_root} for changes (Ctrl+C to stop)", fg=typer.colors.CYAN))
    project_config = load_project_config(project_root)
    settings = apply_project_settings(settings, project_config)
    _run_watch(project_root, storage, settings, project_config, include, exclude)


def _open_existing_storage() -> tuple[Path, ProjectStorage]:
    project_root, storage = _resolve_project(Path.cwd())
    if not storage.db_path.exists():
        _err("No index found. Run `symtext index .` first.")
        raise typer.Exit(1)
    return project_root, storage


@app.command()
def query(
    cypher: str = typer.Argument(..., help="Cypher query to execute"),
) -> None:
    _, storage = _open_existing_storage()
    db = GraphDB(storage.db_path)
    try:
        with db.read_transaction():
            rows = db.query(cypher)
        typer.echo(json.dumps(rows, indent=2, default=str))
    finally:
        db.close()


@app.command()
def explain(
    cypher: str = typer.Argument(..., help="Cypher query to explain"),
) -> None:
    _, storage = _open_existing_storage()
    db = GraphDB(storage.db_path)
    try:
        stripped = cypher.lstrip()
        plan_cypher = stripped if stripped.upper().startswith("EXPLAIN") else f"EXPLAIN {cypher}"
        with db.read_transaction():
            rows = db.query(plan_cypher)
        typer.echo(json.dumps(rows, indent=2, default=str))
    finally:
        db.close()


@app.command()
def mcp(
    watch: bool = typer.Option(
        True,
        "--watch/--no-watch",
        "-w",
        help="Watch for file changes and update the index in the background",
    ),
) -> None:
    settings = Settings()
    apply_process_priority(settings.process_priority)
    cwd = Path.cwd()
    from symtext.mcp.lifecycle import run_mcp, run_refused_mcp

    if is_refused_directory(cwd):
        asyncio.run(run_refused_mcp(cwd))
        return

    project_root, storage = _resolve_project(cwd)
    _setup_logging(settings, storage.log_path)
    project_config = load_project_config(project_root)
    settings = apply_project_settings(settings, project_config)

    asyncio.run(
        run_mcp(
            project_root=project_root,
            storage=storage,
            settings=settings,
            project_config=project_config,
            watch=watch,
            run_index=_run_index,
            collect_files=_collect_files,
        )
    )


@app.command()
def stats() -> None:
    _, storage = _open_existing_storage()

    db = GraphDB(storage.db_path)
    try:
        s = db.stats()
        typer.echo(typer.style("Code Graph Statistics", fg=typer.colors.GREEN, bold=True))
        typer.echo("=" * 40)
        typer.echo(f"Total nodes: {typer.style(str(s['total_nodes']), bold=True)}")
        typer.echo(f"Total edges: {typer.style(str(s['total_edges']), bold=True)}")
        if s["nodes"]:
            typer.echo(typer.style("\nNodes:", fg=typer.colors.CYAN))
            for label, count in sorted(s["nodes"].items()):
                typer.echo(f"  {label:15s} {count:>6d}")
        if s["edges"]:
            typer.echo(typer.style("\nEdges:", fg=typer.colors.CYAN))
            for etype, count in sorted(s["edges"].items()):
                typer.echo(f"  {etype:15s} {count:>6d}")
    finally:
        db.close()


@app.command("list")
def list_cmd(
    rebuild: bool = typer.Option(
        False,
        "-r",
        "--rebuild",
        help="Regenerate the registry by scanning per-project records.",
    ),
    json_out: bool = typer.Option(False, "-j", "--json", help="Emit JSON instead of the formatted table."),
) -> None:
    entries = registry.rebuild() if rebuild else registry.load()

    if json_out:
        typer.echo(json.dumps({h: e.to_json() for h, e in entries.items()}, indent=2, default=str))
        return

    if not entries:
        typer.echo("No projects indexed yet.")
        return

    rows = sorted(entries.items(), key=lambda kv: kv[1].last_opened_at, reverse=True)
    hash_w = max(len("HASH"), max(len(h) for h, _ in rows))
    name_w = max(len("NAME"), max(len(e.project_name or "?") for _, e in rows))
    lang_w = max(len("LANG"), max(len(e.primary_language or "-") for _, e in rows))

    header = f"{'HASH':<{hash_w}}  {'NAME':<{name_w}}  {'LANG':<{lang_w}}  PATH"
    typer.echo(typer.style(header, bold=True))
    typer.echo("-" * (hash_w + name_w + lang_w + 8))
    for h, entry in rows:
        typer.echo(
            f"{h:<{hash_w}}  "
            f"{(entry.project_name or '?'):<{name_w}}  "
            f"{(entry.primary_language or '-'):<{lang_w}}  "
            f"{entry.project_path}"
        )


@app.command()
def doctor(
    json_out: Annotated[bool, typer.Option("-j", "--json", help="Emit JSON instead of formatted text")] = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet", help="Print only issues; suppress full report")] = False,
    global_only: Annotated[
        bool, typer.Option("-g", "--global", help="Diagnose global state only (no project)")
    ] = False,
    check: Annotated[
        str | None,
        typer.Option(
            "--check",
            help="Run one named check (hash_dir/project_json/index_db/locks/config/env)",
        ),
    ] = None,
) -> None:
    from symtext.doctor import render_human, run_doctor

    try:
        report = run_doctor(Path.cwd(), only=check, global_only=global_only)
    except ValueError as exc:
        _err(str(exc))
        raise typer.Exit(2) from exc

    if json_out:
        typer.echo(json.dumps(report.to_json(), indent=2, default=str))
    else:
        typer.echo(render_human(report, quiet=quiet))

    raise typer.Exit(1 if report.has_issues else 0)


@app.command("gc")
def gc_cmd(
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Actually delete orphaned hash dirs (default is dry-run)"),
    ] = False,
    json_out: Annotated[bool, typer.Option("-j", "--json", help="Emit JSON instead of a formatted table")] = False,
) -> None:
    from symtext import gc as gc_mod

    removed, skipped = gc_mod.collect(force=force)

    if json_out:
        typer.echo(
            json.dumps(
                {
                    "removed": [c.to_json() for c in removed],
                    "skipped": [c.to_json() for c in skipped],
                    "dry_run": not force,
                },
                indent=2,
                default=str,
            )
        )
        return

    if not removed and not skipped:
        typer.echo("No orphaned hash dirs detected.")
        return

    if removed:
        total = sum(c.size_bytes for c in removed)
        typer.echo(
            typer.style(
                f"Removed {len(removed)} hash dir(s), freed {total / 1024 / 1024:.1f} MB",
                fg=typer.colors.GREEN,
            )
        )
        for c in removed:
            typer.echo(f"  {c.project_hash}  {c.project_path or '(unknown)'}  [{c.reason}]")

    if skipped:
        verb = "Would remove" if not force else "Skipped (locked)"
        total = sum(c.size_bytes for c in skipped)
        typer.echo(
            typer.style(
                f"{verb}: {len(skipped)} hash dir(s), {total / 1024 / 1024:.1f} MB",
                fg=typer.colors.YELLOW,
            )
        )
        for c in skipped:
            extra = f"locked by {c.lock_holder}" if c.locked else c.reason
            typer.echo(f"  {c.project_hash}  {c.project_path or '(unknown)'}  [{extra}]")
        if not force:
            typer.echo()
            typer.echo("Re-run with --force to actually delete.")
