from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from symtext.mcp.tools_schema import _DEFAULT_LIMIT, _MAX_DEPTH, _MAX_LIMIT
from symtext.parser.parser import detect_language, parse_bytes


def _int_arg(args: dict[str, Any], key: str, default: int, *, min_val: int, max_val: int) -> int:
    raw = args.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(min_val, min(max_val, value))


_PROJECT_ROOT: Path | None = None


def set_project_root(root: Path | None) -> None:
    global _PROJECT_ROOT
    _PROJECT_ROOT = root.resolve() if root is not None else None


def _within_root(path: str) -> bool:
    if not path:
        return False
    root_path = _PROJECT_ROOT if _PROJECT_ROOT is not None else Path(os.getcwd()).resolve()
    candidate = Path(path) if os.path.isabs(path) else root_path / path
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    return resolved == root_path or resolved.is_relative_to(root_path)


def _to_db_path(path: str) -> str:
    if not path:
        return path
    if _PROJECT_ROOT is None:
        if os.path.isabs(path) or path.startswith("/"):
            return path.replace("\\", "/")
        return os.path.abspath(path).replace(os.sep, "/")
    p = Path(path)
    if not p.is_absolute():
        rel = p.as_posix()
    else:
        try:
            rel = p.resolve().relative_to(_PROJECT_ROOT).as_posix()
        except ValueError:
            return p.as_posix()
    return "" if rel in (".", "") else rel


def _to_fs_path(db_path: str) -> Path:
    p = Path(db_path)
    if p.is_absolute() or _PROJECT_ROOT is None:
        return p
    return _PROJECT_ROOT / p


def _resolve_or_error(
    db: Any,
    name: str,
    label: str,
    path: str | None = None,
    prop: str = "name",
) -> tuple[str, str | None] | dict[str, Any]:
    matches = db.resolve_symbol(name, label, prop=prop)

    if path and len(matches) > 1:
        filtered = [m for m in matches if m.get("path") == path]
        if filtered:
            matches = filtered

    if not matches:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"No {label} matching '{name}' found. Try search_symbols to discover available names.",
                }
            ],
            "isError": True,
        }

    if len(matches) == 1:
        return (matches[0]["name"], matches[0].get("path"))

    match_list = [f"  - {m['name']} ({m.get('path', '?')}:{m.get('line_number', '?')})" for m in matches[:15]]
    extra = f"\n  ... and {len(matches) - 15} more" if len(matches) > 15 else ""
    return {
        "content": [
            {
                "type": "text",
                "text": f"Multiple {label} nodes match '{name}'. "
                f"Provide a 'path' to disambiguate or use a more specific name:\n" + "\n".join(match_list) + extra,
            }
        ],
        "isError": True,
    }


def _truncate_docstring(doc: str | None) -> str:
    if not doc:
        return ""
    return doc.split("\n", 1)[0].strip()


def _maybe_truncate(results: list[Any], total: int, limit: int) -> list[Any] | dict[str, Any]:
    if total <= limit:
        return results
    return {
        "results": results,
        "total": total,
        "truncated": True,
        "limit": limit,
    }


def _is_test_path(path: str) -> bool:
    basename = os.path.basename(path)
    if any(
        d in path
        for d in (
            "/test/",
            "/tests/",
            "/__tests__/",
            "/spec/",
            "/fixtures/",
            "/testdata/",
            "/mock/",
            "/mocks/",
            "/e2e/",
            "/integration/",
            "/benchmark/",
            "/benchmarks/",
        )
    ):
        return True
    if basename.startswith("test_") or basename == "conftest.py":
        return True
    stem = basename.rsplit(".", 1)[0] if "." in basename else basename
    if stem.endswith(("_test", "_spec", ".test", ".spec")):
        return True
    parts = basename.split(".")
    return len(parts) >= 3 and parts[-2] in ("test", "spec")


def _extract_context_lines(file_path: str, line_number: int, context: int = 1) -> str | None:
    if not _within_root(file_path):
        return None
    try:
        raw = _to_fs_path(file_path).read_bytes()
    except OSError:
        return None
    lines = raw.decode("utf-8", errors="replace").splitlines()
    start = max(0, line_number - 1 - context)
    end = min(len(lines), line_number + context)
    return "\n".join(lines[start:end])


def _is_likely_entrypoint(symbol: dict[str, Any]) -> bool:
    name = symbol.get("name", "")
    if name.startswith("__") and name.endswith("__"):
        return True
    decorators = symbol.get("decorators") or []
    return bool(decorators)


def _git(args: list[str], cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _git_bytes(args: list[str], cwd: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _key_symbols(syms: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    keyed: dict[tuple[str, str, int], dict[str, Any]] = {}
    for s in sorted(syms, key=lambda x: x.get("line") or 0):
        name = s.get("name", "")
        ctx = s.get("class_context", "") or ""
        counts[(name, ctx)] = counts.get((name, ctx), 0) + 1
        keyed[(name, ctx, counts[(name, ctx)])] = s
    return keyed


def _parsed_to_sym_rows(result: Any, path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fn in result.functions:
        rows.append({
            "name": fn.name,
            "class_context": fn.class_context,
            "line": fn.line_number,
            "end_line": fn.end_line_number,
            "content_hash": fn.content_hash,
            "kind": "function",
            "path": path,
        })
    for cls in result.classes:
        rows.append({
            "name": cls.name,
            "class_context": "",
            "line": cls.line_number,
            "end_line": cls.end_line_number,
            "content_hash": cls.content_hash,
            "kind": "class",
            "path": path,
        })
    return rows


_MAX_SOURCE_LINES = 50


def _extract_source(
    db: Any,
    symbol: dict[str, Any],
) -> dict[str, Any]:
    file_path = symbol.get("path")
    start = symbol.get("line_number", 0)
    end = symbol.get("end_line_number", 0)
    if not file_path or not start or not end:
        return {}
    if not _within_root(file_path):
        return {}

    try:
        raw = _to_fs_path(file_path).read_bytes()
    except OSError:
        return {}

    current_hash = hashlib.sha256(raw).hexdigest()
    file_nodes = db.find_nodes("File", path=file_path)
    stored_hash = file_nodes[0].get("content_hash", "") if file_nodes else ""

    if current_hash != stored_hash:
        reindexed = _reindex_file(db, file_path)
        if not reindexed:
            return {}
        return {"source_reindexed": True}

    lines = raw.decode("utf-8", errors="replace").splitlines()
    source_lines = lines[start - 1 : end]

    result: dict[str, Any] = {}
    total = len(source_lines)
    if total > _MAX_SOURCE_LINES:
        result["source"] = "\n".join(source_lines[:_MAX_SOURCE_LINES])
        result["source_note"] = f"... ({total - _MAX_SOURCE_LINES} more lines)"
    else:
        result["source"] = "\n".join(source_lines)
    return result


def _reindex_file(db: Any, file_path: str) -> bool:
    from symtext.config import Settings
    from symtext.graph.builder import index_file, resolve_cross_references
    from symtext.parser.parser import parse_file

    if not _within_root(file_path):
        return False

    try:
        result = parse_file(_to_fs_path(file_path), settings=Settings())
        if not result:
            return False
        with db.mutating_session():
            index_file(db, result, project_root=_PROJECT_ROOT)
            resolve_cross_references(db, [result], project_root=_PROJECT_ROOT)
        return True
    except Exception as exc:
        logger.warning("Reindex of {} failed: {}", file_path, exc)
        return False


def _get_importers_for_file(db: Any, file_path: str | None) -> list[dict[str, Any]]:
    if not file_path:
        return []
    stem = os.path.splitext(os.path.basename(file_path))[0]
    if not stem or stem == "__init__":
        stem = os.path.basename(os.path.dirname(file_path))
    return db.importers_of_module(stem) if stem else []


def _resolve_symbol_node(db: Any, name: str, label: str, path: str | None) -> dict[str, Any] | None:
    resolved = _resolve_or_error(db, name, label, path=path)
    if isinstance(resolved, dict):
        return None
    rname, rpath = resolved
    nodes = db.find_nodes(label, name=rname)
    if rpath:
        nodes = [n for n in nodes if n.get("path") == rpath] or nodes
    if not nodes:
        return None
    node: dict[str, Any] = nodes[0]
    node["_label"] = label
    return node


def _summarize(db: Any, args: dict[str, Any]) -> Any:
    path = _to_db_path(args.get("path", os.getcwd()))
    include_tests = args.get("include_tests", False)

    summaries = db.file_summaries(path)

    if not include_tests:
        summaries = [s for s in summaries if not _is_test_path(s.get("path", ""))]

    return summaries


def _search_symbols(db: Any, args: dict[str, Any]) -> Any:
    query = args.get("query", "")
    label = args.get("label")
    limit = _int_arg(args, "limit", 20, min_val=1, max_val=_MAX_LIMIT)
    exclude_paths: list[str] = args.get("exclude_paths", [])
    include_tests = args.get("include_tests", False)
    filter_async = args.get("is_async")
    filter_return_type = args.get("return_type")
    filter_has_arg = args.get("has_arg")

    has_sig_filters = filter_async is not None or filter_return_type or filter_has_arg
    if has_sig_filters and label is None:
        label = "Function"

    fetch_limit = limit * 5 if has_sig_filters else limit * 3
    results = db.search(query, label=label, limit=fetch_limit)

    if exclude_paths:
        results = [r for r in results if not any(exc in r.get("path", "") for exc in exclude_paths)]

    if not include_tests:
        results = [r for r in results if not _is_test_path(r.get("path", ""))]

    if filter_async is not None:
        results = [r for r in results if r.get("is_async") == filter_async]
    if filter_return_type:
        results = [r for r in results if filter_return_type.lower() in (r.get("return_type") or "").lower()]
    if filter_has_arg:
        results = [r for r in results if any(filter_has_arg.lower() in a.lower() for a in (r.get("args") or []))]

    total = len(results)
    return _maybe_truncate(results[:limit], total, limit)


def _get_callers(db: Any, args: dict[str, Any]) -> Any:
    name = args.get("name", "")
    path = args.get("path")
    if path:
        path = _to_db_path(path)
    depth = _int_arg(args, "depth", 1, min_val=0, max_val=_MAX_DEPTH)
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)
    include_tests = args.get("include_tests", False)

    resolved = _resolve_or_error(db, name, "Function", path=path)
    if isinstance(resolved, dict):
        return resolved
    rname, rpath = resolved

    total = db.count_callers(rname, path=rpath)

    if depth == 1:
        results = db.callers_with_context(rname, path=rpath, limit=limit)
        for r in results:
            call_line = r.get("call_site_line")
            caller_path = r.get("caller_path")
            if call_line and caller_path:
                ctx = _extract_context_lines(caller_path, call_line)
                if ctx:
                    r["context"] = ctx
    else:
        results = db.callers(rname, path=rpath, depth=depth, limit=limit)

    if not include_tests:
        results = [r for r in results if not _is_test_path(r.get("caller_path", ""))]
    return _maybe_truncate(results, total, limit)


def _get_callees(db: Any, args: dict[str, Any]) -> Any:
    name = args.get("name", "")
    path = args.get("path")
    if path:
        path = _to_db_path(path)
    depth = _int_arg(args, "depth", 1, min_val=0, max_val=_MAX_DEPTH)
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)
    include_tests = args.get("include_tests", False)

    resolved = _resolve_or_error(db, name, "Function", path=path)
    if isinstance(resolved, dict):
        return resolved
    rname, rpath = resolved

    total = db.count_callees(rname, path=rpath)

    if depth == 1:
        results = db.callees_with_context(rname, path=rpath, limit=limit)
        for r in results:
            call_line = r.get("call_site_line")
            if call_line and rpath:
                ctx = _extract_context_lines(rpath, call_line)
                if ctx:
                    r["context"] = ctx
    else:
        results = db.callees(rname, path=rpath, depth=depth, limit=limit)

    if not include_tests:
        results = [r for r in results if not _is_test_path(r.get("callee_path", ""))]
    return _maybe_truncate(results, total, limit)


def _get_importers(db: Any, args: dict[str, Any]) -> Any:
    module = args.get("module", "")
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)

    resolved = _resolve_or_error(db, module, "Module")
    if isinstance(resolved, dict):
        return resolved
    rname, _ = resolved
    return db.importers_of_module(rname, limit=limit)


def _get_dependencies(db: Any, args: dict[str, Any]) -> Any:
    path = _to_db_path(args.get("path", ""))
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)

    if not path:
        return {
            "content": [{"type": "text", "text": "A 'path' argument is required."}],
            "isError": True,
        }

    return db.imports_from_file(path, limit=limit)


def _path_between(db: Any, args: dict[str, Any]) -> Any:
    source = args.get("source", "")
    target = args.get("target", "")
    source_path = args.get("source_path")
    target_path = args.get("target_path")
    max_depth = _int_arg(args, "max_depth", 10, min_val=1, max_val=_MAX_DEPTH)

    if source_path:
        source_path = _to_db_path(source_path)
    if target_path:
        target_path = _to_db_path(target_path)

    resolved_src = _resolve_or_error(db, source, "Function", path=source_path)
    if isinstance(resolved_src, dict):
        return resolved_src
    src_name, src_path = resolved_src

    resolved_tgt = _resolve_or_error(db, target, "Function", path=target_path)
    if isinstance(resolved_tgt, dict):
        return resolved_tgt
    tgt_name, tgt_path = resolved_tgt

    return db.path_between(
        src_name,
        tgt_name,
        source_path=src_path,
        target_path=tgt_path,
        max_depth=max_depth,
    )


def _get_hierarchy(db: Any, args: dict[str, Any]) -> Any:
    name = args.get("name", "")
    direction = args.get("direction", "both")

    resolved = _resolve_or_error(db, name, "Class")
    if isinstance(resolved, dict):
        return resolved
    rname, _ = resolved

    if direction == "both":
        ancestors, descendants = db.ancestors_and_descendants(rname)
        return ancestors + descendants
    if direction == "up":
        return db.ancestors(rname)
    return db.descendants(rname)


def _symbols(db: Any, args: dict[str, Any]) -> Any:
    path = _to_db_path(args.get("path", ""))
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)
    include_tests = args.get("include_tests", False)

    total = db.count_symbols_under(path)
    symbols: list[dict[str, Any]] = []

    func_limit = limit - len(symbols)
    if func_limit > 0:
        symbols.extend(db.functions_under(path, limit=func_limit))

    class_limit = limit - len(symbols)
    if class_limit > 0:
        symbols.extend(db.classes_under(path, limit=class_limit))

    if not include_tests:
        symbols = [s for s in symbols if not _is_test_path(s.get("path", ""))]

    symbols.sort(key=lambda s: (s.get("path", ""), s.get("line", 0)))

    caller_counts = db.caller_counts_under(path)
    callee_counts = db.callee_counts_under(path)

    for sym in symbols:
        if "docstring" in sym:
            sym["docstring"] = _truncate_docstring(sym["docstring"])
        ctx = sym.get("class_context", "")
        if ctx:
            sym["name"] = f"{ctx}.{sym['name']}"
        if "class_context" in sym and not sym["class_context"]:
            del sym["class_context"]
        if sym.get("kind") == "function":
            key = (sym["name"].split(".")[-1], sym.get("path", ""))
            sym["caller_count"] = caller_counts.get(key, 0)
            sym["callee_count"] = callee_counts.get(key, 0)

    return _maybe_truncate(symbols, total, limit)


def _unused_symbols(db: Any, args: dict[str, Any]) -> Any:
    path = args.get("path", "")
    if path:
        path = _to_db_path(path)
    exclude_entrypoints = args.get("exclude_entrypoints", True)
    include_tests = args.get("include_tests", False)
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)

    fetch_limit = limit * 3 if exclude_entrypoints or not include_tests else limit
    results = db.unused_functions(path_prefix=path, limit=fetch_limit)

    if not include_tests:
        results = [r for r in results if not _is_test_path(r.get("path", ""))]
    if exclude_entrypoints:
        results = [r for r in results if not _is_likely_entrypoint(r)]

    for sym in results:
        ctx = sym.get("class_context", "")
        if ctx:
            sym["name"] = f"{ctx}.{sym['name']}"
        if "class_context" in sym and not sym["class_context"]:
            del sym["class_context"]
        if not sym.get("decorators"):
            sym.pop("decorators", None)

    return results[:limit]


def _changed_symbols(db: Any, args: dict[str, Any]) -> Any:
    ref = args.get("ref", "HEAD")
    include_callers = args.get("include_callers", True)
    include_tests = args.get("include_tests", False)
    limit = _int_arg(args, "limit", _DEFAULT_LIMIT, min_val=1, max_val=_MAX_LIMIT)

    if not isinstance(ref, str) or ref.startswith("-"):
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Invalid ref {ref!r}: must be a string not starting with '-'.",
                }
            ],
            "isError": True,
        }

    cwd = os.getcwd()
    repo_root_raw = _git(["rev-parse", "--show-toplevel"], cwd)
    if not repo_root_raw:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "changed_symbols requires a git repository. cwd is not inside one.",
                }
            ],
            "isError": True,
        }
    repo_root = repo_root_raw.strip()

    diff_out = _git(["diff", "--name-only", ref], repo_root)
    if diff_out is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"git diff --name-only {ref} failed. Check that '{ref}' is a valid git ref.",
                }
            ],
            "isError": True,
        }

    changed_rel_paths = [line for line in diff_out.splitlines() if line.strip()]
    repo_root_resolved = Path(repo_root).resolve()

    all_changes: list[dict[str, Any]] = []
    for rel_path in changed_rel_paths:
        if detect_language(Path(rel_path)) is None:
            continue

        joined = (repo_root_resolved / rel_path).resolve()
        if joined != repo_root_resolved and not joined.is_relative_to(repo_root_resolved):
            continue
        abs_path = joined.as_posix()

        ref_bytes = _git_bytes(["show", f"{ref}:{rel_path}"], repo_root)
        ref_rows: list[dict[str, Any]] = []
        if ref_bytes is not None:
            ref_result = parse_bytes(Path(abs_path), ref_bytes)
            if ref_result is not None:
                ref_rows = _parsed_to_sym_rows(ref_result, abs_path)

        cur_rows = db.symbols_with_hashes(abs_path)

        ref_keyed = _key_symbols(ref_rows)
        cur_keyed = _key_symbols(cur_rows)

        for key, sym in cur_keyed.items():
            if key not in ref_keyed:
                all_changes.append({**sym, "change_type": "added"})
            elif sym.get("content_hash") != ref_keyed[key].get("content_hash"):
                all_changes.append({**sym, "change_type": "modified"})

        for key, sym in ref_keyed.items():
            if key not in cur_keyed:
                all_changes.append({**sym, "change_type": "deleted"})

    if not include_tests:
        all_changes = [c for c in all_changes if not _is_test_path(c.get("path", ""))]

    if include_callers:
        for change in all_changes:
            if change.get("kind") != "function":
                continue
            if change["change_type"] == "added":
                continue
            callers = db.callers_with_context(change["name"], path=change.get("path"), limit=20)
            if not include_tests:
                callers = [c for c in callers if not _is_test_path(c.get("caller_path", ""))]
            change["callers"] = callers

    all_changes.sort(key=lambda c: (c.get("path", ""), c.get("kind", ""), c.get("line") or 0))

    for c in all_changes:
        c.pop("end_line", None)

    total = len(all_changes)
    return _maybe_truncate(all_changes[:limit], total, limit)


def _shape(db: Any, _args: dict[str, Any]) -> Any:
    result = db.stats()
    for key in ("CONTAINS_FUNC", "CONTAINS_CLASS"):
        result["edges"].pop(key, None)
    result["languages"] = db.language_breakdown()
    result["directories"] = db.directory_counts()
    return result


def _describe_symbol(db: Any, args: dict[str, Any]) -> Any:
    name = args.get("name", "")
    path = args.get("path")
    depth = _int_arg(args, "depth", 1, min_val=0, max_val=_MAX_DEPTH)
    include_tests = args.get("include_tests", False)
    if path:
        path = _to_db_path(path)

    symbol = _resolve_symbol_node(db, name, "Function", path)
    is_class = False
    if symbol is None:
        symbol = _resolve_symbol_node(db, name, "Class", path)
        is_class = True
    if symbol is None:
        return _resolve_or_error(db, name, "Function", path=path)

    source_info = _extract_source(db, symbol)
    if source_info.get("source_reindexed"):
        label = "Class" if is_class else "Function"
        refreshed = _resolve_symbol_node(db, name, label, path)
        if refreshed:
            symbol = refreshed
            source_info = _extract_source(db, symbol)

    rname = symbol["name"]
    rpath = symbol.get("path")

    if is_class:
        ancestors, descendants = db.ancestors_and_descendants(rname)
        result = {
            "symbol": symbol,
            "ancestors": ancestors,
            "descendants": descendants,
            "importers": _get_importers_for_file(db, rpath),
        }
    else:
        if depth == 1:
            callers, callees = db.callers_and_callees_with_context(rname, path=rpath)
            for r in callers:
                call_line = r.get("call_site_line")
                caller_path = r.get("caller_path")
                if call_line and caller_path:
                    ctx = _extract_context_lines(caller_path, call_line)
                    if ctx:
                        r["context"] = ctx

            for r in callees:
                call_line = r.get("call_site_line")
                if call_line and rpath:
                    ctx = _extract_context_lines(rpath, call_line)
                    if ctx:
                        r["context"] = ctx
        else:
            callers, callees = db.callers_and_callees(rname, path=rpath, depth=depth)

        if not include_tests:
            callers = [r for r in callers if not _is_test_path(r.get("caller_path", ""))]
            callees = [r for r in callees if not _is_test_path(r.get("callee_path", ""))]

        result = {
            "symbol": symbol,
            "callers": callers,
            "callees": callees,
            "importers": _get_importers_for_file(db, rpath),
        }

    if "source" in source_info:
        result["source"] = source_info["source"]
        if "source_note" in source_info:
            result["source_note"] = source_info["source_note"]

    return result


@dataclass(frozen=True)
class ToolDef:
    handler: Any
    recovery_hint: str


_TOOLS: dict[str, ToolDef] = {
    "summarize": ToolDef(
        _summarize,
        "Verify the path exists, or call with no arguments to summarize the whole project.",
    ),
    "search_symbols": ToolDef(_search_symbols, "Try a shorter substring or omit the label filter."),
    "get_callers": ToolDef(
        _get_callers,
        "Try a shorter name substring, or use search_symbols to find available names.",
    ),
    "get_callees": ToolDef(
        _get_callees,
        "Try a shorter name substring, or use search_symbols to find available names.",
    ),
    "get_importers": ToolDef(
        _get_importers,
        "Try a shorter module name substring, or use search_symbols to verify the module exists.",
    ),
    "get_dependencies": ToolDef(_get_dependencies, "Verify the file path exists and has been indexed."),
    "path_between": ToolDef(
        _path_between,
        "Verify both function names exist with search_symbols. "
        "Try increasing max_depth if the path is longer than expected.",
    ),
    "get_hierarchy": ToolDef(
        _get_hierarchy,
        "Try a shorter class name substring, or use search_symbols with label='Class'.",
    ),
    "symbols": ToolDef(_symbols, "Verify the path exists. Try a parent directory or use search_symbols."),
    "unused_symbols": ToolDef(
        _unused_symbols,
        "Verify the path prefix matches indexed files. Try omitting 'path' to scan the whole project.",
    ),
    "changed_symbols": ToolDef(
        _changed_symbols,
        "Ensure cwd is inside a git repo and 'ref' is a valid commit-ish. Try 'HEAD', 'HEAD~1', or a branch name.",
    ),
    "shape": ToolDef(_shape, "This is unexpected — the index may be empty. Run 'symtext index' first."),
    "describe_symbol": ToolDef(
        _describe_symbol,
        "Try a shorter name substring, or use search_symbols to discover names.",
    ),
}
