from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar

from graphdblite import Database, ReadTransaction, WriteTransaction


DB_SCHEMA_VERSION = 1

_NODE_COLUMNS: dict[str, list[str]] = {
    "Metadata": [
        "key",
        "schema_version",
        "symtext_version",
        "created_at",
        "project_root_at_index_time",
    ],
    "File": ["key", "name", "path", "language", "content_hash", "variables"],
    "Function": [
        "key",
        "name",
        "path",
        "line_number",
        "end_line_number",
        "args",
        "annotations",
        "docstring",
        "class_context",
        "cyclomatic_complexity",
        "is_async",
        "return_type",
        "content_hash",
        "language",
    ],
    "Class": [
        "key",
        "name",
        "path",
        "line_number",
        "end_line_number",
        "kind",
        "bases",
        "attributes",
        "docstring",
        "content_hash",
        "language",
    ],
    "Module": ["key", "name"],
}

_EDGE_PROP_COLUMNS: dict[str, list[str]] = {
    "CONTAINS_FUNC": [],
    "CONTAINS_CLASS": [],
    "CALLS": ["line_number"],
    "IMPORTS": ["line_number", "alias", "imported_name"],
    "INHERITS": [],
}

_EDGE_LABELS: dict[str, tuple[str, str]] = {
    "CONTAINS_FUNC": ("File", "Function"),
    "CONTAINS_CLASS": ("File", "Class"),
    "CALLS": ("Function", "Function"),
    "IMPORTS": ("File", "Module"),
    "INHERITS": ("Class", "Class"),
}

_SEARCHABLE_LABELS: list[str] = ["Function", "Class", "File", "Module"]

_METADATA_KEY = "db"


def _return_clause(label: str, var: str = "n") -> str:
    cols = _NODE_COLUMNS[label]
    parts = [f"{var}.{c} AS {c}" for c in cols]
    return "RETURN " + ", ".join(parts)


def _validate_label(label: str) -> None:
    if label not in _NODE_COLUMNS:
        raise ValueError(f"Unknown node label: {label!r}")


def _validate_prop(label: str, prop: str) -> None:
    _validate_label(label)
    if prop not in _NODE_COLUMNS[label]:
        raise ValueError(f"Unknown property {prop!r} on label {label!r}")


def _validate_edge_type(edge_type: str) -> None:
    if edge_type not in _EDGE_PROP_COLUMNS:
        raise ValueError(f"Unknown edge type: {edge_type!r}")


class GraphDB:
    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._tx: WriteTransaction | ReadTransaction | None = None
        if db_path == ":memory:" or str(db_path) == ":memory:":
            self._db: Database = Database.open_memory()
            self._path: Path | None = None
        else:
            p = Path(db_path) if isinstance(db_path, str) else db_path
            p.parent.mkdir(parents=True, exist_ok=True)
            self._db = Database(str(p))
            self._path = p

    def _execute(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if isinstance(self._tx, WriteTransaction):
            return self._tx.execute(cypher, params)
        if isinstance(self._tx, ReadTransaction):
            raise RuntimeError(
                "Write query attempted inside a read transaction. "
                "Open a write transaction (db.transaction()) or run outside any tx."
            )
        return self._db.execute(cypher, params)

    def _query_db(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._tx is not None:
            return self._tx.query(cypher, params)
        return self._db.query(cypher, params)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._tx is not None:
            yield
            return
        with self._db.begin_write() as tx:
            self._tx = tx
            try:
                yield
            finally:
                self._tx = None

    @contextmanager
    def read_transaction(self) -> Iterator[None]:
        if self._tx is not None:
            yield
            return
        with self._db.begin_read() as tx:
            self._tx = tx
            try:
                yield
            finally:
                self._tx = None

    def batch_create_nodes(
        self,
        label: str,
        nodes: list[dict[str, Any]],
    ) -> dict[str, int]:
        if not isinstance(self._tx, WriteTransaction):
            raise RuntimeError("batch_create_nodes must be called inside a write transaction")
        keys = [n["key"] for n in nodes]
        ids: list[int] = self._tx.batch_create_nodes(label, nodes)
        return dict(zip(keys, ids, strict=True))

    def batch_create_edges(
        self,
        edge_type: str,
        edges: list[tuple[int, int, Any]],
    ) -> None:
        if not isinstance(self._tx, WriteTransaction):
            raise RuntimeError("batch_create_edges must be called inside a write transaction")
        batch: list[tuple[int, int] | tuple[int, int, dict[str, Any]]] = []
        for edge in edges:
            src_id, tgt_id, props = edge[0], edge[1], edge[2] if len(edge) > 2 else None
            if props:
                batch.append((src_id, tgt_id, props))
            else:
                batch.append((src_id, tgt_id))
        self._tx.batch_create_edges(edge_type, batch)

    _SECONDARY_INDEXES: ClassVar[list[tuple[str, str]]] = [
        ("Function", "key"),
        ("Function", "name"),
        ("Function", "path"),
        ("File", "key"),
        ("File", "name"),
        ("File", "path"),
        ("Class", "key"),
        ("Class", "name"),
        ("Module", "key"),
        ("Module", "name"),
    ]

    def create_indexes(self) -> None:
        with self.transaction():
            if not isinstance(self._tx, WriteTransaction):
                return
            for label, prop in self._SECONDARY_INDEXES:
                self._tx.create_index(label, prop)

    def drop_indexes(self) -> None:
        with self.transaction():
            if not isinstance(self._tx, WriteTransaction):
                return
            for label, prop in self._SECONDARY_INDEXES:
                with contextlib.suppress(Exception):
                    self._tx.drop_index(label, prop)

    @contextmanager
    def mutating_session(self) -> Iterator[None]:
        self.drop_indexes()
        try:
            with self.transaction():
                yield
        finally:
            self.create_indexes()

    def init_metadata(
        self,
        symtext_version: str,
        project_root: str,
        created_at: str,
    ) -> None:
        self.merge_node(
            "Metadata",
            _METADATA_KEY,
            {
                "schema_version": DB_SCHEMA_VERSION,
                "symtext_version": symtext_version,
                "created_at": created_at,
                "project_root_at_index_time": project_root,
            },
        )

    def get_metadata(self) -> dict[str, Any] | None:
        return self.get_node("Metadata", _METADATA_KEY)

    def schema_version(self) -> int | None:
        meta = self.get_metadata()
        if not meta:
            return None
        val = meta.get("schema_version")
        return int(val) if val is not None else None

    def merge_node(self, label: str, key: str, props: dict[str, Any]) -> str:
        _validate_label(label)
        for k in props:
            _validate_prop(label, k)
        params: dict[str, Any] = {"_key": key, **props}
        set_clause = ", ".join(f"n.{k} = ${k}" for k in props) if props else ""

        if set_clause:
            cypher = f"MERGE (n:{label} {{key: $_key}}) ON CREATE SET {set_clause} ON MATCH SET {set_clause}"
        else:
            cypher = f"MERGE (n:{label} {{key: $_key}})"

        self._execute(cypher, params)
        return key

    def get_node(self, label: str, key: str) -> dict[str, Any] | None:
        _validate_label(label)
        ret = _return_clause(label)
        cypher = f"MATCH (n:{label} {{key: $key}}) {ret}"
        rows = self._query_db(cypher, {"key": key})
        return rows[0] if rows else None

    def find_nodes(self, label: str, **filters: Any) -> list[dict[str, Any]]:
        _validate_label(label)
        for k in filters:
            _validate_prop(label, k)
        where_parts = [f"n.{k} = ${k}" for k in filters]
        where = " WHERE " + " AND ".join(where_parts) if where_parts else ""
        ret = _return_clause(label)
        cypher = f"MATCH (n:{label}){where} {ret}"
        return self._query_db(cypher, filters or None)

    def delete_nodes_by_prop(self, label: str, prop: str, value: Any) -> int:
        _validate_prop(label, prop)
        params = {"value": value}
        count_cypher = f"MATCH (n:{label}) WHERE n.{prop} = $value RETURN count(*) AS cnt"
        rows = self._query_db(count_cypher, params)
        count: int = rows[0]["cnt"] if rows else 0
        if count == 0:
            return 0
        del_cypher = f"MATCH (n:{label}) WHERE n.{prop} = $value DETACH DELETE n"
        self._execute(del_cypher, params)
        return count

    def merge_edge(
        self,
        edge_type: str,
        src_label: str,
        src_key: str,
        tgt_label: str,
        tgt_key: str,
        props: dict[str, Any] | None = None,
    ) -> None:
        _validate_edge_type(edge_type)
        _validate_label(src_label)
        _validate_label(tgt_label)
        prop_cols = _EDGE_PROP_COLUMNS[edge_type]
        params: dict[str, Any] = {"src_key": src_key, "tgt_key": tgt_key}
        set_parts: list[str] = []
        if props:
            for col in prop_cols:
                if col in props:
                    params[col] = props[col]
                    set_parts.append(f"r.{col} = ${col}")

        match = f"MATCH (a:{src_label} {{key: $src_key}}), (b:{tgt_label} {{key: $tgt_key}})"
        if set_parts:
            set_clause = ", ".join(set_parts)
            self._execute(
                f"{match} MERGE (a)-[r:{edge_type}]->(b) ON CREATE SET {set_clause} ON MATCH SET {set_clause}",
                params,
            )
        else:
            self._execute(f"{match} MERGE (a)-[:{edge_type}]->(b)", params)

    def create_edge(
        self,
        edge_type: str,
        src_label: str,
        src_key: str,
        tgt_label: str,
        tgt_key: str,
        props: dict[str, Any] | None = None,
    ) -> None:
        _validate_edge_type(edge_type)
        _validate_label(src_label)
        _validate_label(tgt_label)
        prop_cols = _EDGE_PROP_COLUMNS[edge_type]
        params: dict[str, Any] = {"src_key": src_key, "tgt_key": tgt_key}
        inline_props: list[str] = []
        if props:
            for col in prop_cols:
                if col in props:
                    params[col] = props[col]
                    inline_props.append(f"{col}: ${col}")

        match = f"MATCH (a:{src_label} {{key: $src_key}}), (b:{tgt_label} {{key: $tgt_key}})"
        if inline_props:
            prop_str = ", ".join(inline_props)
            self._execute(f"{match} CREATE (a)-[:{edge_type} {{{prop_str}}}]->(b)", params)
        else:
            self._execute(f"{match} CREATE (a)-[:{edge_type}]->(b)", params)

    def get_edges(
        self,
        edge_type: str,
        src_label: str,
        tgt_label: str,
        src_key: str | None = None,
        tgt_key: str | None = None,
    ) -> list[dict[str, Any]]:
        _validate_edge_type(edge_type)
        _validate_label(src_label)
        _validate_label(tgt_label)
        prop_cols = _EDGE_PROP_COLUMNS[edge_type]

        params: dict[str, Any] = {}
        where_parts: list[str] = []
        if src_key is not None:
            where_parts.append("a.key = $src_key")
            params["src_key"] = src_key
        if tgt_key is not None:
            where_parts.append("b.key = $tgt_key")
            params["tgt_key"] = tgt_key
        where = " WHERE " + " AND ".join(where_parts) if where_parts else ""

        ret_parts = [
            "a.key AS src_key",
            "b.key AS tgt_key",
            f"'{edge_type}' AS type",
        ]
        for col in prop_cols:
            ret_parts.append(f"r.{col} AS {col}")

        ret = "RETURN " + ", ".join(ret_parts)
        cypher = f"MATCH (a:{src_label})-[r:{edge_type}]->(b:{tgt_label}){where} {ret}"
        return self._query_db(cypher, params or None)

    def search(
        self,
        query: str,
        label: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if label is not None:
            _validate_label(label)
        results: list[dict[str, Any]] = []
        labels = [label] if label else _SEARCHABLE_LABELS

        for lbl in labels:
            remaining = limit - len(results)
            if remaining <= 0:
                break

            where = "n.name CONTAINS $q"
            if lbl in ("Function", "Class"):
                where += " OR n.docstring CONTAINS $q"

            ret = _return_clause(lbl)
            cypher = f"MATCH (n:{lbl}) WHERE {where} {ret} LIMIT {remaining}"
            for row in self._query_db(cypher, {"q": query}):
                row["_label"] = lbl
                results.append(row)
        return results[:limit]

    def query(self, cypher: str) -> list[dict[str, Any]]:
        return self._query_db(cypher)

    def stats(self) -> dict[str, Any]:
        nodes: dict[str, int] = {}
        for lbl in _NODE_COLUMNS:
            if lbl == "Metadata":
                continue
            rows = self._query_db(f"MATCH (n:{lbl}) RETURN count(*) AS cnt")
            cnt: int = rows[0]["cnt"] if rows else 0
            if cnt > 0:
                nodes[lbl] = cnt

        edges: dict[str, int] = {}
        for etype, (src_lbl, tgt_lbl) in _EDGE_LABELS.items():
            rows = self._query_db(f"MATCH (:{src_lbl})-[r:{etype}]->(:{tgt_lbl}) RETURN count(*) AS cnt")
            cnt = rows[0]["cnt"] if rows else 0
            if cnt > 0:
                edges[etype] = cnt

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": sum(nodes.values()),
            "total_edges": sum(edges.values()),
        }

    def resolve_symbol(
        self,
        value: str,
        label: str,
        prop: str = "name",
    ) -> list[dict[str, Any]]:
        _validate_prop(label, prop)
        ret = _return_clause(label)
        params = {"value": value}

        exact = self._query_db(f"MATCH (n:{label}) WHERE n.{prop} = $value {ret}", params)
        if exact:
            return exact

        return self._query_db(f"MATCH (n:{label}) WHERE n.{prop} CONTAINS $value {ret}", params)

    def _call_query(
        self,
        *,
        direction: str,
        name: str,
        path: str | None,
        depth: int,
        with_ctx: bool,
        count_only: bool,
        limit: int | None,
    ) -> tuple[str, dict[str, Any]]:
        is_callers = direction == "callers"
        named, other = ("b", "a") if is_callers else ("a", "b")
        edge = "[r:CALLS]" if with_ctx else "[:CALLS]"
        edge_pattern = edge if depth == 1 else f"[:CALLS*1..{depth}]"
        params: dict[str, Any] = {"name": name}
        path_filter = ""
        if path:
            path_filter = f" AND {named}.path = $path"
            params["path"] = path

        match = (
            f"MATCH (a:Function)-{edge_pattern}->(b:Function {{name: $name}})"
            if is_callers
            else f"MATCH (a:Function {{name: $name}})-{edge_pattern}->(b:Function)"
        )
        where = f" WHERE {other} <> {named}{path_filter}"
        if count_only:
            return match + where + " RETURN count(*) AS cnt", params

        col = "caller" if is_callers else "callee"
        returns = (
            f" RETURN DISTINCT {other}.name AS {col}, {other}.path AS {col}_path, {other}.line_number AS {col}_line"
        )
        if with_ctx:
            returns += ", r.line_number AS call_site_line"
        tail = f" LIMIT {limit}" if limit is not None else ""
        return match + where + returns + tail, params

    def callers(
        self,
        target_name: str,
        path: str | None = None,
        depth: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        max_depth = depth if depth and depth > 0 else 64
        cypher, params = self._call_query(
            direction="callers",
            name=target_name,
            path=path,
            depth=max_depth,
            with_ctx=False,
            count_only=False,
            limit=limit,
        )
        return self._query_db(cypher, params)

    def callees(
        self,
        source_name: str,
        path: str | None = None,
        depth: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        max_depth = depth if depth and depth > 0 else 64
        cypher, params = self._call_query(
            direction="callees",
            name=source_name,
            path=path,
            depth=max_depth,
            with_ctx=False,
            count_only=False,
            limit=limit,
        )
        return self._query_db(cypher, params)

    def path_between(
        self,
        source_name: str,
        target_name: str,
        source_path: str | None = None,
        target_path: str | None = None,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"src_name": source_name, "tgt_name": target_name}
        src_filter = ""
        tgt_filter = ""
        if source_path:
            src_filter = ", path: $src_path"
            params["src_path"] = source_path
        if target_path:
            tgt_filter = ", path: $tgt_path"
            params["tgt_path"] = target_path
        cypher = (
            f"MATCH (src:Function {{name: $src_name{src_filter}}}), "
            f"(dst:Function {{name: $tgt_name{tgt_filter}}}), "
            f"p = shortestPath((src)-[:CALLS*1..{max_depth}]->(dst)) "
            f"RETURN nodes(p) AS path_nodes"
        )
        rows = self._query_db(cypher, params)
        if not rows or not rows[0].get("path_nodes"):
            return []

        path_nodes: list[dict[str, Any]] = rows[0]["path_nodes"]
        return [
            {
                "step": i,
                "name": n.get("name"),
                "path": n.get("path"),
                "line_number": n.get("line_number"),
            }
            for i, n in enumerate(path_nodes)
        ]

    def top_connected(self, path_prefix: str = "", limit: int = 10) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        where = ""
        if path_prefix:
            where = " WHERE b.path STARTS WITH $prefix"
            params["prefix"] = path_prefix
        cypher = (
            f"MATCH (a:Function)-[:CALLS]->(b:Function){where}"
            f" RETURN b.name AS name, b.path AS path, count(*) AS caller_count"
            f" ORDER BY caller_count DESC"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, params or None)

    def top_imported_modules(self, path_prefix: str = "", limit: int = 10) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        where = ""
        if path_prefix:
            where = " WHERE f.path STARTS WITH $prefix"
            params["prefix"] = path_prefix
        cypher = (
            f"MATCH (f:File)-[:IMPORTS]->(m:Module){where}"
            f" RETURN m.name AS module, count(*) AS importer_count"
            f" ORDER BY importer_count DESC"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, params or None)

    def callers_with_context(
        self,
        target_name: str,
        path: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        cypher, params = self._call_query(
            direction="callers",
            name=target_name,
            path=path,
            depth=1,
            with_ctx=True,
            count_only=False,
            limit=limit,
        )
        return self._query_db(cypher, params)

    def callees_with_context(
        self,
        source_name: str,
        path: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        cypher, params = self._call_query(
            direction="callees",
            name=source_name,
            path=path,
            depth=1,
            with_ctx=True,
            count_only=False,
            limit=limit,
        )
        return self._query_db(cypher, params)

    def callers_and_callees_with_context(
        self,
        name: str,
        path: str | None = None,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        params: dict[str, Any] = {"name": name}
        path_inline = ""
        if path:
            path_inline = ", path: $path"
            params["path"] = path
        fn = f"{{name: $name{path_inline}}}"
        cypher = (
            f"MATCH (other:Function)-[r:CALLS]->(fn:Function {fn}) "
            f"WHERE other <> fn "
            f"RETURN DISTINCT 'caller' AS rel, other.name AS other_name,"
            f" other.path AS other_path, other.line_number AS other_line,"
            f" r.line_number AS call_site_line "
            f"UNION ALL "
            f"MATCH (fn:Function {fn})-[r:CALLS]->(other:Function) "
            f"WHERE other <> fn "
            f"RETURN DISTINCT 'callee' AS rel, other.name AS other_name,"
            f" other.path AS other_path, other.line_number AS other_line,"
            f" r.line_number AS call_site_line "
            f"LIMIT {limit}"
        )
        rows = self._query_db(cypher, params)

        callers: list[dict[str, Any]] = []
        callees: list[dict[str, Any]] = []
        for row in rows:
            if row.get("rel") == "caller":
                callers.append({
                    "caller": row.get("other_name"),
                    "caller_path": row.get("other_path"),
                    "caller_line": row.get("other_line"),
                    "call_site_line": row.get("call_site_line"),
                })
            else:
                callees.append({
                    "callee": row.get("other_name"),
                    "callee_path": row.get("other_path"),
                    "callee_line": row.get("other_line"),
                    "call_site_line": row.get("call_site_line"),
                })
        return callers, callees

    def callers_and_callees(
        self,
        name: str,
        path: str | None = None,
        depth: int | None = None,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        max_depth = depth if depth and depth > 0 else 64
        params: dict[str, Any] = {"name": name}
        path_inline = ""
        if path:
            path_inline = ", path: $path"
            params["path"] = path
        fn = f"{{name: $name{path_inline}}}"
        cypher = (
            f"MATCH (other:Function)-[:CALLS*1..{max_depth}]->(fn:Function {fn}) "
            f"WHERE other <> fn "
            f"RETURN DISTINCT 'caller' AS rel, other.name AS other_name,"
            f" other.path AS other_path, other.line_number AS other_line "
            f"UNION ALL "
            f"MATCH (fn:Function {fn})-[:CALLS*1..{max_depth}]->(other:Function) "
            f"WHERE other <> fn "
            f"RETURN DISTINCT 'callee' AS rel, other.name AS other_name,"
            f" other.path AS other_path, other.line_number AS other_line "
            f"LIMIT {limit}"
        )
        rows = self._query_db(cypher, params)

        callers: list[dict[str, Any]] = []
        callees: list[dict[str, Any]] = []
        for row in rows:
            if row.get("rel") == "caller":
                callers.append({
                    "caller": row.get("other_name"),
                    "caller_path": row.get("other_path"),
                    "caller_line": row.get("other_line"),
                })
            else:
                callees.append({
                    "callee": row.get("other_name"),
                    "callee_path": row.get("other_path"),
                    "callee_line": row.get("other_line"),
                })
        return callers, callees

    def ancestors_and_descendants(
        self,
        class_name: str,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        cypher = (
            f"MATCH (a:Class {{name: $name}})-[:INHERITS*1..]->(b:Class) "
            f"RETURN DISTINCT 'ancestor' AS rel, b.name AS name, b.path AS path "
            f"UNION ALL "
            f"MATCH (a:Class)-[:INHERITS*1..]->(b:Class {{name: $name}}) "
            f"RETURN DISTINCT 'descendant' AS rel, a.name AS name, a.path AS path "
            f"LIMIT {limit}"
        )
        rows = self._query_db(cypher, {"name": class_name})

        ancestors: list[dict[str, Any]] = []
        descendants: list[dict[str, Any]] = []
        for row in rows:
            rel = row.get("rel")
            entry = {
                "name": row.get("name"),
                "path": row.get("path"),
                "relation": rel,
            }
            if rel == "ancestor":
                ancestors.append(entry)
            else:
                descendants.append(entry)
        return ancestors, descendants

    def imports_from_file(self, file_path: str, limit: int = 50) -> list[dict[str, Any]]:
        cypher = (
            f"MATCH (f:File {{path: $path}})"
            f"-[i:IMPORTS]->(m:Module)"
            f" RETURN m.name AS module, i.imported_name AS imported_name,"
            f" i.alias AS alias, i.line_number AS line_number"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, {"path": file_path})

    def importers_of_module(self, module_name: str, limit: int = 50) -> list[dict[str, Any]]:
        cypher = (
            f"MATCH (f:File)-[i:IMPORTS]->(m:Module {{name: $name}})"
            f" RETURN f.path AS file_path, i.imported_name AS imported_name,"
            f" i.alias AS alias, i.line_number AS line_number"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, {"name": module_name})

    def ancestors(self, class_name: str, limit: int = 50) -> list[dict[str, Any]]:
        cypher = (
            f"MATCH (a:Class {{name: $name}})"
            f"-[:INHERITS*1..]->(b:Class)"
            f" RETURN DISTINCT b.name AS name, b.path AS path,"
            f" 'ancestor' AS relation"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, {"name": class_name})

    def descendants(self, class_name: str, limit: int = 50) -> list[dict[str, Any]]:
        cypher = (
            f"MATCH (a:Class)-[:INHERITS*1..]->"
            f"(b:Class {{name: $name}})"
            f" RETURN DISTINCT a.name AS name, a.path AS path,"
            f" 'descendant' AS relation"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, {"name": class_name})

    def functions_under(self, path_prefix: str, limit: int = 50) -> list[dict[str, Any]]:
        cypher = (
            f"MATCH (f:File)-[:CONTAINS_FUNC]->(fn:Function)"
            f" WHERE f.path STARTS WITH $prefix"
            f" RETURN fn.name AS name, fn.path AS path,"
            f" fn.line_number AS line, 'function' AS kind,"
            f" fn.class_context AS class_context,"
            f" fn.args AS args, fn.docstring AS docstring,"
            f" fn.annotations AS decorators,"
            f" fn.is_async AS is_async, fn.return_type AS return_type"
            f" ORDER BY fn.path, fn.line_number"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, {"prefix": path_prefix})

    def classes_under(self, path_prefix: str, limit: int = 50) -> list[dict[str, Any]]:
        cypher = (
            f"MATCH (f:File)-[:CONTAINS_CLASS]->(c:Class)"
            f" WHERE f.path STARTS WITH $prefix"
            f" RETURN c.name AS name, c.path AS path,"
            f" c.line_number AS line, 'class' AS kind,"
            f" c.bases AS bases, c.docstring AS docstring"
            f" ORDER BY c.path, c.line_number"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, {"prefix": path_prefix})

    def symbols_with_hashes(self, file_path: str) -> list[dict[str, Any]]:
        params = {"path": file_path}
        fn_rows = self._query_db(
            "MATCH (f:File {path: $path})-[:CONTAINS_FUNC]->(fn:Function)"
            " RETURN fn.name AS name, fn.class_context AS class_context,"
            " fn.line_number AS line, fn.end_line_number AS end_line,"
            " fn.content_hash AS content_hash, 'function' AS kind",
            params,
        )
        cls_rows = self._query_db(
            "MATCH (f:File {path: $path})-[:CONTAINS_CLASS]->(c:Class)"
            " RETURN c.name AS name, '' AS class_context,"
            " c.line_number AS line, c.end_line_number AS end_line,"
            " c.content_hash AS content_hash, 'class' AS kind",
            params,
        )
        return fn_rows + cls_rows

    def count_symbols_under(self, path_prefix: str) -> int:
        params = {"prefix": path_prefix}
        func_rows = self._query_db(
            "MATCH (f:File)-[:CONTAINS_FUNC]->(fn:Function) WHERE f.path STARTS WITH $prefix RETURN count(*) AS cnt",
            params,
        )
        class_rows = self._query_db(
            "MATCH (f:File)-[:CONTAINS_CLASS]->(c:Class) WHERE f.path STARTS WITH $prefix RETURN count(*) AS cnt",
            params,
        )
        fc = func_rows[0]["cnt"] if func_rows else 0
        cc = class_rows[0]["cnt"] if class_rows else 0
        return fc + cc

    def unused_functions(
        self,
        path_prefix: str = "",
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        where_path = ""
        if path_prefix:
            where_path = " AND fn.path STARTS WITH $prefix"
            params["prefix"] = path_prefix
        cypher = (
            f"MATCH (fn:Function)"
            f" WHERE NOT EXISTS {{ ()-[:CALLS]->(fn) }}{where_path}"
            f" RETURN fn.name AS name, fn.path AS path,"
            f" fn.line_number AS line, fn.class_context AS class_context,"
            f" fn.annotations AS decorators"
            f" LIMIT {limit}"
        )
        return self._query_db(cypher, params or None)

    def caller_counts_under(self, path_prefix: str) -> dict[tuple[str, str], int]:
        rows = self._query_db(
            "MATCH (caller:Function)-[:CALLS]->(fn:Function)"
            " WHERE fn.path STARTS WITH $prefix"
            " RETURN fn.name AS name, fn.path AS path, count(caller) AS cnt",
            {"prefix": path_prefix},
        )
        return {(r["name"], r["path"]): r["cnt"] for r in rows}

    def callee_counts_under(self, path_prefix: str) -> dict[tuple[str, str], int]:
        rows = self._query_db(
            "MATCH (fn:Function)-[:CALLS]->(callee:Function)"
            " WHERE fn.path STARTS WITH $prefix"
            " RETURN fn.name AS name, fn.path AS path, count(callee) AS cnt",
            {"prefix": path_prefix},
        )
        return {(r["name"], r["path"]): r["cnt"] for r in rows}

    def count_callers(self, target_name: str, path: str | None = None) -> int:
        cypher, params = self._call_query(
            direction="callers",
            name=target_name,
            path=path,
            depth=1,
            with_ctx=False,
            count_only=True,
            limit=None,
        )
        rows = self._query_db(cypher, params)
        return rows[0]["cnt"] if rows else 0

    def count_callees(self, source_name: str, path: str | None = None) -> int:
        cypher, params = self._call_query(
            direction="callees",
            name=source_name,
            path=path,
            depth=1,
            with_ctx=False,
            count_only=True,
            limit=None,
        )
        rows = self._query_db(cypher, params)
        return rows[0]["cnt"] if rows else 0

    def directory_counts(self) -> list[dict[str, Any]]:
        from collections import Counter

        dir_files: Counter[str] = Counter()
        dir_funcs: Counter[str] = Counter()
        dir_classes: Counter[str] = Counter()

        for row in self._query_db("MATCH (f:File) RETURN f.path AS path"):
            d = str(PurePosixPath(row["path"]).parent)
            dir_files[d] += 1

        for row in self._query_db(
            "MATCH (f:File)-[:CONTAINS_FUNC]->(fn:Function) RETURN f.path AS path, count(*) AS cnt"
        ):
            d = str(PurePosixPath(row["path"]).parent)
            dir_funcs[d] += row["cnt"]

        for row in self._query_db("MATCH (f:File)-[:CONTAINS_CLASS]->(c:Class) RETURN f.path AS path, count(*) AS cnt"):
            d = str(PurePosixPath(row["path"]).parent)
            dir_classes[d] += row["cnt"]

        all_dirs = sorted(set(dir_files) | set(dir_funcs) | set(dir_classes))
        return [
            {
                "directory": d,
                "files": dir_files.get(d, 0),
                "functions": dir_funcs.get(d, 0),
                "classes": dir_classes.get(d, 0),
            }
            for d in all_dirs
        ]

    def language_breakdown(self, path_prefix: str = "") -> dict[str, int]:
        params: dict[str, Any] = {}
        where = ""
        if path_prefix:
            where = " WHERE f.path STARTS WITH $prefix"
            params["prefix"] = path_prefix
        rows = self._query_db(
            f"MATCH (f:File){where} RETURN f.language AS language, count(*) AS cnt",
            params or None,
        )
        return {r["language"]: r["cnt"] for r in rows if r.get("language")}

    def file_summaries(self, path_prefix: str, top_n: int = 5) -> list[dict[str, Any]]:
        params = {"prefix": path_prefix}

        lang_rows = self._query_db(
            "MATCH (f:File) WHERE f.path STARTS WITH $prefix RETURN f.path AS path, f.language AS language",
            params,
        )
        file_lang = {r["path"]: r["language"] for r in lang_rows}

        func_count_rows = self._query_db(
            "MATCH (f:File)-[:CONTAINS_FUNC]->(fn:Function)"
            " WHERE f.path STARTS WITH $prefix"
            " RETURN f.path AS path, count(*) AS cnt",
            params,
        )
        file_func_count = {r["path"]: r["cnt"] for r in func_count_rows}

        class_rows = self.classes_under(path_prefix, limit=500)
        file_classes: dict[str, list[dict[str, Any]]] = {}
        for c in class_rows:
            fp = c.get("path", "")
            file_classes.setdefault(fp, []).append({
                "name": c["name"],
                "bases": c.get("bases", []),
            })

        top_rows = self._query_db(
            "MATCH (a:Function)-[:CALLS]->(b:Function)"
            " WHERE b.path STARTS WITH $prefix"
            " WITH b.path AS path, b.name AS name,"
            " b.class_context AS class_context, count(*) AS caller_count"
            " ORDER BY path, caller_count DESC"
            " RETURN path, COLLECT(name) AS top_functions",
            params,
        )
        file_top: dict[str, list[str]] = {r["path"]: r["top_functions"][:top_n] for r in top_rows}

        in_rows = self._query_db(
            "MATCH (a:Function)-[:CALLS]->(b:Function)"
            " WHERE b.path STARTS WITH $prefix"
            " RETURN b.path AS path, count(*) AS cnt",
            params,
        )
        file_in: dict[str, int] = {r["path"]: r["cnt"] for r in in_rows}

        out_rows = self._query_db(
            "MATCH (a:Function)-[:CALLS]->(b:Function)"
            " WHERE a.path STARTS WITH $prefix"
            " RETURN a.path AS path, count(*) AS cnt",
            params,
        )
        file_out: dict[str, int] = {r["path"]: r["cnt"] for r in out_rows}

        all_files = sorted(set(file_lang) | set(file_func_count))
        return [
            {
                "path": fp,
                "language": file_lang.get(fp, ""),
                "function_count": file_func_count.get(fp, 0),
                "classes": file_classes.get(fp, []),
                "top_functions": file_top.get(fp, []),
                "total_callers": file_in.get(fp, 0),
                "total_callees": file_out.get(fp, 0),
            }
            for fp in all_files
        ]

    def delete_orphan_modules(self) -> int:
        count_rows = self._query_db("MATCH (m:Module) WHERE NOT EXISTS { ()-[:IMPORTS]->(m) } RETURN count(*) AS cnt")
        count: int = count_rows[0]["cnt"] if count_rows else 0
        if count == 0:
            return 0
        self._execute("MATCH (m:Module) WHERE NOT EXISTS { ()-[:IMPORTS]->(m) } DELETE m")
        return count

    def close(self) -> None:
        self._db.close()

    def snapshot_to(self, path: Path | str) -> None:
        self._db.snapshot_to(str(path))

    def atomic_swap(self, live_db_path: Path) -> None:
        live_db_path.parent.mkdir(parents=True, exist_ok=True)
        staging = live_db_path.with_name(live_db_path.name + ".new")
        staging.unlink(missing_ok=True)
        self.snapshot_to(staging)
        os.replace(staging, live_db_path)
        for suffix in ("-wal", "-shm"):
            Path(str(live_db_path) + suffix).unlink(missing_ok=True)
