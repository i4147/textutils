from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from loguru import logger

if TYPE_CHECKING:
    from symtext.db.graphdb import GraphDB
    from symtext.parser.parser import FileParseResult


_T = TypeVar("_T")


def build_key(label: str, *parts: str | int) -> str:
    return f"{label}:" + ":".join(str(p) for p in parts)


def _pick_best(targets: list[_T], prefer_path: str, path_of: Callable[[_T], str]) -> _T:
    if len(targets) == 1:
        return targets[0]
    same_file = [t for t in targets if path_of(t) == prefer_path]
    return same_file[0] if same_file else targets[0]


def _file_node_props(result: FileParseResult, path_str: str) -> dict[str, Any]:
    return {
        "name": result.path.name,
        "path": path_str,
        "language": result.language,
        "content_hash": result.content_hash,
        "variables": result.variables,
    }


def _function_node_props(fn: Any, path_str: str, language: str) -> dict[str, Any]:
    return {
        "name": fn.name,
        "path": path_str,
        "line_number": fn.line_number,
        "end_line_number": fn.end_line_number,
        "args": fn.args,
        "annotations": fn.decorators,
        "docstring": fn.docstring,
        "class_context": fn.class_context,
        "cyclomatic_complexity": float(fn.cyclomatic_complexity),
        "is_async": fn.is_async,
        "return_type": fn.return_type,
        "content_hash": fn.content_hash,
        "language": language,
    }


def _class_node_props(cls: Any, path_str: str, language: str) -> dict[str, Any]:
    return {
        "name": cls.name,
        "path": path_str,
        "line_number": cls.line_number,
        "end_line_number": cls.end_line_number,
        "kind": cls.kind,
        "bases": cls.bases,
        "attributes": cls.attributes,
        "docstring": cls.docstring,
        "content_hash": cls.content_hash,
        "language": language,
    }


def relpath_for_db(file_path: Path, project_root: Path | None) -> str | None:
    if project_root is None:
        return file_path.as_posix()
    try:
        rel = file_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return None
    return rel.as_posix()


def index_file(
    db: GraphDB,
    result: FileParseResult,
    *,
    fresh: bool = False,
    project_root: Path | None = None,
) -> None:
    path_str = relpath_for_db(result.path, project_root)
    if path_str is None:
        logger.warning("Skipping out-of-tree file: {}", result.path)
        return
    _add_edge = db.create_edge if fresh else db.merge_edge

    with db.transaction():
        if not fresh:
            clear_file(db, path_str)

        file_key = build_key("File", path_str)
        db.merge_node("File", file_key, _file_node_props(result, path_str))

        for fn in result.functions:
            fn_key = build_key("Function", path_str, fn.name, fn.line_number)
            db.merge_node("Function", fn_key, _function_node_props(fn, path_str, result.language))
            _add_edge("CONTAINS_FUNC", "File", file_key, "Function", fn_key)

        for cls in result.classes:
            cls_key = build_key("Class", path_str, cls.name, cls.line_number)
            db.merge_node("Class", cls_key, _class_node_props(cls, path_str, result.language))
            _add_edge("CONTAINS_CLASS", "File", file_key, "Class", cls_key)

        for imp in result.imports:
            mod_key = build_key("Module", imp.module)
            db.merge_node("Module", mod_key, {"name": imp.module})
            _add_edge(
                "IMPORTS",
                "File",
                file_key,
                "Module",
                mod_key,
                {
                    "line_number": imp.line_number,
                    "alias": imp.alias,
                    "imported_name": imp.imported_name,
                },
            )


def resolve_cross_references(
    db: GraphDB,
    all_results: list[FileParseResult] | None = None,
    *,
    fresh: bool = False,
    project_root: Path | None = None,
) -> None:
    if all_results:
        _resolve_calls(db, all_results, fresh=fresh, project_root=project_root)
    _resolve_inherits(db, fresh=fresh)


def _resolve_calls(
    db: GraphDB,
    all_results: list[FileParseResult],
    *,
    fresh: bool = False,
    project_root: Path | None = None,
) -> None:
    _add_edge = db.create_edge if fresh else db.merge_edge

    all_functions = db.find_nodes("Function")
    func_by_name: dict[str, list[dict[str, Any]]] = {}
    for fn in all_functions:
        name = fn.get("name", "")
        if name:
            func_by_name.setdefault(name, []).append(fn)

    calls_created = 0
    with db.transaction():
        for result in all_results:
            path_str = relpath_for_db(result.path, project_root)
            if path_str is None:
                continue
            local_funcs: dict[str, Any] = {fn.name: fn for fn in result.functions}
            for call in result.calls:
                if not call.caller:
                    continue
                caller_fn = local_funcs.get(call.caller)
                if caller_fn is None:
                    continue
                caller_key = build_key("Function", path_str, caller_fn.name, caller_fn.line_number)

                targets = func_by_name.get(call.name, [])
                if not targets:
                    continue
                target = _pick_best(targets, path_str, lambda t: t.get("path", ""))

                _add_edge(
                    "CALLS",
                    "Function",
                    caller_key,
                    "Function",
                    target["key"],
                    {"line_number": call.line_number},
                )
                calls_created += 1

    logger.debug("Created {} CALLS edges", calls_created)


def _resolve_inherits(db: GraphDB, *, fresh: bool = False) -> None:
    _add_edge = db.create_edge if fresh else db.merge_edge

    all_classes = db.find_nodes("Class")
    class_by_name: dict[str, list[dict[str, Any]]] = {}
    for cls in all_classes:
        name = cls.get("name", "")
        if name:
            class_by_name.setdefault(name, []).append(cls)

    inherits_created = 0
    with db.transaction():
        for cls in all_classes:
            bases = cls.get("bases", [])
            if not bases:
                continue
            src_key = cls["key"]
            for base_name in bases:
                targets = class_by_name.get(base_name, [])
                if not targets:
                    continue
                target = _pick_best(targets, cls.get("path", ""), lambda t: t.get("path", ""))
                _add_edge("INHERITS", "Class", src_key, "Class", target["key"])
                inherits_created += 1

    logger.debug(
        "Created {} INHERITS edges for {} classes",
        inherits_created,
        len(all_classes),
    )


def batch_index(
    db: GraphDB,
    all_results: list[FileParseResult],
    *,
    project_root: Path | None = None,
) -> int:
    file_nodes: list[dict[str, Any]] = []
    func_nodes: list[dict[str, Any]] = []
    class_nodes: list[dict[str, Any]] = []
    module_map: dict[str, dict[str, Any]] = {}

    contains_func_edges: list[tuple[str, str]] = []
    contains_class_edges: list[tuple[str, str]] = []
    import_edges: list[tuple[str, str, dict[str, Any]]] = []

    for result in all_results:
        path_str = relpath_for_db(result.path, project_root)
        if path_str is None:
            logger.warning("Skipping out-of-tree file: {}", result.path)
            continue
        file_key = build_key("File", path_str)
        file_nodes.append({"key": file_key, **_file_node_props(result, path_str)})

        for fn in result.functions:
            fn_key = build_key("Function", path_str, fn.name, fn.line_number)
            func_nodes.append({"key": fn_key, **_function_node_props(fn, path_str, result.language)})
            contains_func_edges.append((file_key, fn_key))

        for cls in result.classes:
            cls_key = build_key("Class", path_str, cls.name, cls.line_number)
            class_nodes.append({"key": cls_key, **_class_node_props(cls, path_str, result.language)})
            contains_class_edges.append((file_key, cls_key))

        for imp in result.imports:
            mod_key = build_key("Module", imp.module)
            module_map[imp.module] = {"key": mod_key, "name": imp.module}
            import_edges.append((
                file_key,
                mod_key,
                {
                    "line_number": imp.line_number,
                    "alias": imp.alias,
                    "imported_name": imp.imported_name,
                },
            ))

    module_nodes = list(module_map.values())

    with db.transaction():
        file_ids = db.batch_create_nodes("File", file_nodes)
        func_ids = db.batch_create_nodes("Function", func_nodes)
        class_ids = db.batch_create_nodes("Class", class_nodes)
        module_ids = db.batch_create_nodes("Module", module_nodes)
        all_ids = {**file_ids, **func_ids, **class_ids, **module_ids}

        db.batch_create_edges(
            "CONTAINS_FUNC",
            [(all_ids[s], all_ids[t], None) for s, t in contains_func_edges],
        )
        db.batch_create_edges(
            "CONTAINS_CLASS",
            [(all_ids[s], all_ids[t], None) for s, t in contains_class_edges],
        )
        db.batch_create_edges(
            "IMPORTS",
            [(all_ids[s], all_ids[t], p) for s, t, p in import_edges],
        )

        func_by_name: dict[str, list[dict[str, Any]]] = {}
        for node in func_nodes:
            func_by_name.setdefault(node["name"], []).append(node)

        call_edges: list[tuple[int, int, dict[str, Any]]] = []
        for result in all_results:
            path_str = relpath_for_db(result.path, project_root)
            if path_str is None:
                continue
            local_funcs: dict[str, Any] = {fn.name: fn for fn in result.functions}
            for call in result.calls:
                if not call.caller:
                    continue
                caller_fn = local_funcs.get(call.caller)
                if caller_fn is None:
                    continue
                caller_key = build_key("Function", path_str, caller_fn.name, caller_fn.line_number)

                targets = func_by_name.get(call.name, [])
                if not targets:
                    continue
                target = _pick_best(targets, path_str, lambda t: t.get("path", ""))

                caller_id = all_ids.get(caller_key)
                target_id = all_ids.get(target["key"])
                if caller_id is not None and target_id is not None:
                    call_edges.append((caller_id, target_id, {"line_number": call.line_number}))

        if call_edges:
            db.batch_create_edges("CALLS", call_edges)
        logger.debug("Created {} CALLS edges (batch)", len(call_edges))

        class_by_name: dict[str, list[dict[str, Any]]] = {}
        for node in class_nodes:
            class_by_name.setdefault(node["name"], []).append(node)

        inherits_edges: list[tuple[int, int, None]] = []
        for node in class_nodes:
            for base_name in node.get("bases", []):
                targets = class_by_name.get(base_name, [])
                if not targets:
                    continue
                target = _pick_best(targets, node.get("path", ""), lambda t: t.get("path", ""))
                src_id = all_ids.get(node["key"])
                tgt_id = all_ids.get(target["key"])
                if src_id is not None and tgt_id is not None:
                    inherits_edges.append((src_id, tgt_id, None))

        if inherits_edges:
            db.batch_create_edges("INHERITS", inherits_edges)
        logger.debug("Created {} INHERITS edges (batch)", len(inherits_edges))

    return len(all_results)


def streaming_batch_index(
    db: GraphDB,
    parse_iter: Any,
    *,
    project_root: Path,
    batch_size: int = 500,
    batch_max_bytes: int = 100 * 1024 * 1024,
    on_progress: Any = None,
) -> int:
    all_ids: dict[str, int] = {}
    call_refs: list[tuple[str, str, int, str, int]] = []
    inherit_refs: list[tuple[str, str]] = []

    batch: list[FileParseResult] = []
    batch_bytes = 0
    indexed = 0

    def _flush() -> None:
        nonlocal batch_bytes
        if not batch:
            return
        ids = _ingest_batch_nodes_and_simple_edges(db, batch, project_root=project_root)
        all_ids.update(ids)
        for result in batch:
            path_str = relpath_for_db(result.path, project_root)
            if path_str is None:
                continue
            for fn in result.functions:
                fn_key = build_key("Function", path_str, fn.name, fn.line_number)
                for call in result.calls:
                    if call.caller == fn.name:
                        call_refs.append((fn_key, call.name, call.line_number, path_str, fn.line_number))
            for cls in result.classes:
                cls_key = build_key("Class", path_str, cls.name, cls.line_number)
                for base in cls.bases:
                    inherit_refs.append((cls_key, base))
        batch.clear()
        batch_bytes = 0

    for result in parse_iter:
        if result is None:
            continue
        batch.append(result)
        batch_bytes += result.size_bytes or 4096
        indexed += 1
        if on_progress is not None:
            on_progress(indexed, indexed)
        if len(batch) >= batch_size or batch_bytes >= batch_max_bytes:
            _flush()

    _flush()

    _resolve_streaming_xrefs(db, all_ids, call_refs, inherit_refs)
    return indexed


def _ingest_batch_nodes_and_simple_edges(
    db: GraphDB,
    results: list[FileParseResult],
    *,
    project_root: Path,
) -> dict[str, int]:
    file_nodes: list[dict[str, Any]] = []
    func_nodes: list[dict[str, Any]] = []
    class_nodes: list[dict[str, Any]] = []
    module_map: dict[str, dict[str, Any]] = {}

    contains_func: list[tuple[str, str]] = []
    contains_class: list[tuple[str, str]] = []
    import_edges: list[tuple[str, str, dict[str, Any]]] = []

    for result in results:
        path_str = relpath_for_db(result.path, project_root)
        if path_str is None:
            logger.warning("Skipping out-of-tree file: {}", result.path)
            continue
        file_key = build_key("File", path_str)
        file_nodes.append({"key": file_key, **_file_node_props(result, path_str)})
        for fn in result.functions:
            fn_key = build_key("Function", path_str, fn.name, fn.line_number)
            func_nodes.append({"key": fn_key, **_function_node_props(fn, path_str, result.language)})
            contains_func.append((file_key, fn_key))
        for cls in result.classes:
            cls_key = build_key("Class", path_str, cls.name, cls.line_number)
            class_nodes.append({"key": cls_key, **_class_node_props(cls, path_str, result.language)})
            contains_class.append((file_key, cls_key))
        for imp in result.imports:
            mod_key = build_key("Module", imp.module)
            module_map.setdefault(imp.module, {"key": mod_key, "name": imp.module})
            import_edges.append((
                file_key,
                mod_key,
                {
                    "line_number": imp.line_number,
                    "alias": imp.alias,
                    "imported_name": imp.imported_name,
                },
            ))

    ids: dict[str, int] = {}
    with db.transaction():
        if file_nodes:
            ids.update(db.batch_create_nodes("File", file_nodes))
        if func_nodes:
            ids.update(db.batch_create_nodes("Function", func_nodes))
        if class_nodes:
            ids.update(db.batch_create_nodes("Class", class_nodes))
        if module_map:
            ids.update(db.batch_create_nodes("Module", list(module_map.values())))
        if contains_func:
            db.batch_create_edges("CONTAINS_FUNC", [(ids[s], ids[t], None) for s, t in contains_func])
        if contains_class:
            db.batch_create_edges("CONTAINS_CLASS", [(ids[s], ids[t], None) for s, t in contains_class])
        if import_edges:
            db.batch_create_edges("IMPORTS", [(ids[s], ids[t], p) for s, t, p in import_edges])
    return ids


def _resolve_streaming_xrefs(
    db: GraphDB,
    all_ids: dict[str, int],
    call_refs: list[tuple[str, str, int, str, int]],
    inherit_refs: list[tuple[str, str]],
) -> None:
    funcs_by_name: dict[str, list[tuple[str, str]]] = {}
    classes_by_name: dict[str, list[tuple[str, str]]] = {}
    for key in all_ids:
        if key.startswith("Function:"):
            parts = key.split(":")
            if len(parts) >= 4:
                path, name = parts[1], parts[2]
                funcs_by_name.setdefault(name, []).append((key, path))
        elif key.startswith("Class:"):
            parts = key.split(":")
            if len(parts) >= 4:
                path, name = parts[1], parts[2]
                classes_by_name.setdefault(name, []).append((key, path))

    call_edges: list[tuple[int, int, dict[str, Any]]] = []
    for caller_key, target_name, call_line, caller_path, _ in call_refs:
        targets = funcs_by_name.get(target_name)
        if not targets:
            continue
        target_key = _pick_best(targets, caller_path, lambda t: t[1])[0]
        src_id = all_ids.get(caller_key)
        tgt_id = all_ids.get(target_key)
        if src_id is not None and tgt_id is not None:
            call_edges.append((src_id, tgt_id, {"line_number": call_line}))

    inherits_edges: list[tuple[int, int, None]] = []
    for cls_key, base_name in inherit_refs:
        targets = classes_by_name.get(base_name)
        if not targets:
            continue
        cls_path = cls_key.split(":")[1] if ":" in cls_key else ""
        target_key = _pick_best(targets, cls_path, lambda t: t[1])[0]
        src_id = all_ids.get(cls_key)
        tgt_id = all_ids.get(target_key)
        if src_id is not None and tgt_id is not None:
            inherits_edges.append((src_id, tgt_id, None))

    if call_edges or inherits_edges:
        with db.transaction():
            if call_edges:
                db.batch_create_edges("CALLS", call_edges)
            if inherits_edges:
                db.batch_create_edges("INHERITS", inherits_edges)
    logger.debug("streaming xrefs: {} CALLS, {} INHERITS", len(call_edges), len(inherits_edges))


def clear_file(db: GraphDB, path: str) -> None:
    db.delete_nodes_by_prop("Function", "path", path)
    db.delete_nodes_by_prop("Class", "path", path)
    db.delete_nodes_by_prop("File", "path", path)
    _cleanup_orphan_modules(db)


def _cleanup_orphan_modules(db: GraphDB) -> None:
    db.delete_orphan_modules()
