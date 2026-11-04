from __future__ import annotations

import contextlib
import json
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from symtext import __version__
from symtext.config import (
    resolve_settings,
    user_global_config_path,
)
from symtext.db.graphdb import DB_SCHEMA_VERSION, GraphDB
from symtext.lock import read_holder, try_acquire
from symtext.paths import (
    BUILD_MARKERS,
    STRONG_AI_MARKERS,
    canonical_project_path,
    find_project_root,
    is_refused_directory,
    project_hash,
)
from symtext.storage import ProjectStorage, base_dir


@dataclass
class CheckResult:
    name: str
    ok: bool
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    suggestion: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DoctorReport:
    symtext_version: str
    cwd: str
    project_root: str | None
    detection_reason: str
    project_hash: str | None
    refused: bool
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(not c.ok for c in self.checks)

    def to_json(self) -> dict[str, Any]:
        return {
            "symtext_version": self.symtext_version,
            "cwd": self.cwd,
            "project_root": self.project_root,
            "detection_reason": self.detection_reason,
            "project_hash": self.project_hash,
            "refused": self.refused,
            "has_issues": self.has_issues,
            "checks": [c.to_json() for c in self.checks],
        }


def _detection_reason(cwd: Path, root: Path) -> str:
    from symtext.paths import SYMTEXT_ROOT_MARKER

    marker = root / SYMTEXT_ROOT_MARKER
    if marker.is_file() or marker.is_dir():
        return f"explicit marker ({SYMTEXT_ROOT_MARKER})"
    if (root / ".git").exists():
        return "VCS root (.git)"
    for vcs in (".hg", ".jj", ".svn", ".bzr", "CVS", "_darcs", ".fossil"):
        if (root / vcs).exists():
            return f"VCS root ({vcs})"
    for name in BUILD_MARKERS:
        if (root / name).is_file():
            return f"build/manifest ({name})"
    for name in STRONG_AI_MARKERS:
        if (root / name).is_file():
            return f"AI marker ({name})"
    if root == cwd.resolve():
        return "lenient cwd fallback"
    return "unknown"


def _format_age(iso_string: str) -> str:
    try:
        when = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError:
        return iso_string
    now = datetime.now(UTC)
    delta = now - when
    seconds = int(delta.total_seconds())
    if seconds < 60:
        ago = f"{seconds}s ago"
    elif seconds < 3600:
        ago = f"{seconds // 60}m ago"
    elif seconds < 86_400:
        ago = f"{seconds // 3600}h ago"
    else:
        ago = f"{seconds // 86_400}d ago"
    return f"{when.strftime('%Y-%m-%d %H:%M:%S')} ({ago})"


def _check_hash_dir(storage: ProjectStorage) -> CheckResult:
    exists = storage.project_dir.is_dir()
    return CheckResult(
        name="hash_dir",
        ok=exists,
        summary=("exists" if exists else "missing — project not indexed yet"),
        details={"path": str(storage.project_dir)},
        suggestion=None if exists else "Run `symtext index .` or start `symtext mcp`.",
    )


def _check_project_json(storage: ProjectStorage) -> CheckResult:
    if not storage.project_json_path.is_file():
        return CheckResult(
            name="project_json",
            ok=False,
            summary="missing",
            details={"path": str(storage.project_json_path)},
            suggestion="Indexing will create this on the next run.",
        )
    try:
        record = storage.load_record()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return CheckResult(
            name="project_json",
            ok=False,
            summary=f"unreadable ({exc})",
            details={"path": str(storage.project_json_path)},
        )
    assert record is not None
    return CheckResult(
        name="project_json",
        ok=True,
        summary=(
            f"schema_version={record.schema_version}, name={record.project_name!r}, lang={record.primary_language!r}"
        ),
        details=record.to_json(),
    )


def _check_index_db(storage: ProjectStorage) -> CheckResult:
    if not storage.db_path.is_file():
        return CheckResult(
            name="index_db",
            ok=False,
            summary="missing",
            details={"path": str(storage.db_path)},
            suggestion="Run `symtext index .` or open the project with `symtext mcp`.",
        )
    size_bytes = storage.db_path.stat().st_size
    try:
        db = GraphDB(storage.db_path)
        try:
            stats = db.stats()
            recorded_schema = db.schema_version()
            metadata = db.get_metadata() or {}
        finally:
            db.close()
    except Exception as exc:
        return CheckResult(
            name="index_db",
            ok=False,
            summary=f"open failed: {exc}",
            details={"path": str(storage.db_path)},
        )

    schema_ok = recorded_schema == DB_SCHEMA_VERSION
    summary = (
        f"{size_bytes / 1024 / 1024:.1f} MB, "
        f"{stats['nodes'].get('File', 0)} files, "
        f"{stats['total_nodes']} symbols, "
        f"{stats['total_edges']} relationships"
    )
    return CheckResult(
        name="index_db",
        ok=schema_ok,
        summary=summary,
        details={
            "path": str(storage.db_path),
            "size_bytes": size_bytes,
            "schema_version": recorded_schema,
            "expected_schema_version": DB_SCHEMA_VERSION,
            "created_at": metadata.get("created_at"),
            "symtext_version": metadata.get("symtext_version"),
            "stats": stats,
        },
        suggestion=(
            None
            if schema_ok
            else f"Schema drift: DB v{recorded_schema} vs code v{DB_SCHEMA_VERSION}. "
            "Will reindex on next `symtext mcp` start."
        ),
    )


def _check_locks(storage: ProjectStorage) -> CheckResult:
    info: dict[str, Any] = {}
    issues: list[str] = []

    for label, path in (
        ("watcher_lock", storage.watcher_lock_path),
        ("index_lock", storage.index_lock_path),
    ):
        if not path.exists():
            info[label] = {"state": "free"}
            continue
        handle = try_acquire(path, tag="doctor-probe")
        if handle is None:
            info[label] = {
                "state": "held",
                "holder": read_holder(path) or "(unknown)",
                "path": str(path),
            }
            if label == "index_lock":
                issues.append("indexing in progress")
        else:
            handle.release()
            info[label] = {"state": "free", "path": str(path)}

    return CheckResult(
        name="locks",
        ok=not issues,
        summary=", ".join(issues)
        if issues
        else "watcher=" + info["watcher_lock"]["state"] + ", index=" + info["index_lock"]["state"],
        details=info,
    )


def _check_config(project_root: Path | None) -> CheckResult:
    resolved = resolve_settings(project_root)
    src_counts: dict[str, int] = {}
    for src in resolved.sources.values():
        src_counts[src] = src_counts.get(src, 0) + 1
    pieces = [f"{n} {s}" for s, n in sorted(src_counts.items())]
    return CheckResult(
        name="config",
        ok=True,
        summary=", ".join(pieces),
        details={
            "user_global_path": str(user_global_config_path()),
            "user_global_exists": user_global_config_path().is_file(),
            "per_project_path": (str(ProjectStorage(project_root).config_path) if project_root is not None else None),
            "per_project_exists": (
                ProjectStorage(project_root).config_path.is_file() if project_root is not None else False
            ),
            "sources": resolved.sources,
            "values": resolved.settings.model_dump(),
        },
    )


def _check_environment() -> CheckResult:
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    uvx_path = shutil.which("uvx")
    tree_sitter_ok = True
    tree_sitter_error: str | None = None
    try:
        import tree_sitter_language_pack
    except ImportError as exc:
        tree_sitter_ok = False
        tree_sitter_error = str(exc)

    return CheckResult(
        name="environment",
        ok=tree_sitter_ok,
        summary=f"Python {py}, uvx={'OK' if uvx_path else 'not found'}, "
        f"tree-sitter={'OK' if tree_sitter_ok else 'MISSING'}",
        details={
            "python_version": py,
            "platform": sys.platform,
            "uvx_path": uvx_path,
            "tree_sitter_language_pack": tree_sitter_ok,
            "tree_sitter_error": tree_sitter_error,
        },
    )


_CHECK_REGISTRY: dict[str, str] = {
    "hash_dir": "_check_hash_dir",
    "project_json": "_check_project_json",
    "index_db": "_check_index_db",
    "locks": "_check_locks",
    "config": "_check_config",
    "env": "_check_environment",
}


def run_doctor(
    cwd: Path,
    *,
    only: str | None = None,
    global_only: bool = False,
) -> DoctorReport:
    cwd = cwd.resolve()
    refused = is_refused_directory(cwd)

    project_root: Path | None
    detection_reason = "refused (Tier 3 hard-refuse)" if refused else ""
    if refused:
        project_root = None
        storage: ProjectStorage | None = None
    else:
        try:
            project_root = find_project_root(canonical_project_path(cwd))
        except (FileNotFoundError, ValueError, OSError) as exc:
            project_root = None
            detection_reason = f"detection failed: {exc}"
        if project_root is not None:
            detection_reason = _detection_reason(cwd, project_root)
        storage = ProjectStorage(project_root) if project_root else None

    report = DoctorReport(
        symtext_version=__version__,
        cwd=str(cwd),
        project_root=str(project_root) if project_root else None,
        detection_reason=detection_reason,
        project_hash=project_hash(project_root) if project_root else None,
        refused=refused,
    )

    if global_only:
        report.checks.append(_check_config(None))
        report.checks.append(_check_environment())
        return report

    if refused:
        report.checks.append(_check_environment())
        return report

    assert storage is not None

    available: dict[str, Any] = {
        "hash_dir": lambda: _check_hash_dir(storage),
        "project_json": lambda: _check_project_json(storage),
        "index_db": lambda: _check_index_db(storage),
        "locks": lambda: _check_locks(storage),
        "config": lambda: _check_config(project_root),
        "env": lambda: _check_environment(),
    }

    if only is not None:
        if only not in available:
            raise ValueError(f"unknown check '{only}'; available: {', '.join(sorted(available))}")
        report.checks.append(available[only]())
        return report

    for name in ("hash_dir", "project_json", "index_db", "locks", "config", "env"):
        with contextlib.suppress(Exception):
            report.checks.append(available[name]())
    return report


def render_human(report: DoctorReport, *, quiet: bool = False) -> str:
    lines: list[str] = []

    if report.has_issues:
        lines.append(f"⚠ symtext {report.symtext_version} — issues found:")
        lines.append("")
        for i, c in enumerate((x for x in report.checks if not x.ok), start=1):
            lines.append(f"  {i}. {c.name}: {c.summary}")
            if c.suggestion:
                lines.append(f"     → {c.suggestion}")
        lines.append("")
        if quiet:
            return "\n".join(lines)
        lines.append("Details:")

    lines.append(f"symtext {report.symtext_version} — diagnostics")
    lines.append("")
    lines.append(f"Current directory:    {report.cwd}")
    if report.refused:
        lines.append("Project root:         (refused — Tier 3 hard-refuse)")
    elif report.project_root is None:
        lines.append("Project root:         (none — detection failed)")
    else:
        lines.append(f"Project root:         {report.project_root}  ({report.detection_reason})")
        if report.project_hash is not None:
            lines.append(f"Project hash:         {report.project_hash}")
            lines.append(f"Hash dir:             {base_dir() / 'projects' / report.project_hash}")
    lines.append("")

    for c in report.checks:
        marker = "✓" if c.ok else "✗"
        lines.append(f"  [{marker}] {c.name:<14} {c.summary}")
        if c.name == "index_db" and c.ok:
            created = c.details.get("created_at")
            if created:
                lines.append(f"            last indexed: {_format_age(created)}")
        if c.suggestion and not c.ok:
            lines.append(f"            → {c.suggestion}")

    if not report.has_issues:
        lines.append("")
        lines.append("No issues detected.")
    return "\n".join(lines)
