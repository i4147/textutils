from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FILTER_OPS = frozenset({"eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "is_null", "range"})


@dataclass(slots=True)
class IRFilter:
    key: str
    value: Any
    operator: str = "eq"

    def __post_init__(self) -> None:
        if self.operator not in FILTER_OPS:
            raise ValueError(
                f"Unknown filter operator '{self.operator}'. Must be one of: {', '.join(sorted(FILTER_OPS))}"
            )


@dataclass(slots=True)
class IRJoin:
    relation: str
    target: str
    on_left: str
    on_right: str
    fields: list[str] = field(default_factory=list)
    filters: list[IRFilter] = field(default_factory=list)
    join_type: str = "LEFT"


@dataclass(slots=True)
class IRNested:
    relation: str
    target: str
    fields: list[str] = field(default_factory=list)
    filters: list[IRFilter] = field(default_factory=list)
    children: list["IRNested"] = field(default_factory=list)


@dataclass(slots=True)
class IRAggregation:
    function: str
    field: str
    alias: str | None = None


@dataclass
class QueryIR:
    entity: str
    fields: list[str] = field(default_factory=list)
    filters: list[IRFilter] = field(default_factory=list)
    joins: list[IRJoin] = field(default_factory=list)
    nested: list[IRNested] = field(default_factory=list)
    aggregations: list[IRAggregation] = field(default_factory=list)
    group_filters: dict[str, Any] = field(default_factory=dict)
    order_by: str | None = None
    order_dir: str | None = None
    limit: int | None = None
    offset: int | None = None
    target: str = "graphql"
    source_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    distinct: bool = False
    having: list[dict[str, Any]] = field(default_factory=list)
    subqueries: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_query_result(cls, result: "Any", source_text: str = "") -> "QueryIR":
        meta = result.metadata if isinstance(result.metadata, dict) else {}
        entity = meta.get("entity") or meta.get("table") or ""

        raw_filters = meta.get("filters", {})
        flat_filters, group_filters = _split_filters(raw_filters)

        raw_joins: list[dict[str, Any]] = meta.get("joins", [])
        joins = [_join_from_dict(j) for j in raw_joins if isinstance(j, dict)]

        raw_nested: list[dict[str, Any]] = meta.get("nested", [])
        nested = [_nested_from_dict(n) for n in raw_nested if isinstance(n, dict)]

        raw_aggs: list[dict[str, Any]] = meta.get("aggregations", [])
        aggregations = [_agg_from_dict(a) for a in raw_aggs if isinstance(a, dict)]

        return cls(
            entity=entity,
            fields=list(meta.get("fields") or meta.get("columns") or []),
            filters=flat_filters,
            joins=joins,
            nested=nested,
            aggregations=aggregations,
            group_filters=group_filters,
            order_by=meta.get("order_by"),
            order_dir=meta.get("order_dir"),
            limit=meta.get("limit"),
            offset=meta.get("offset"),
            target=result.target,
            source_text=source_text,
            metadata=meta,
            distinct=bool(meta.get("distinct", False)),
            having=list(meta.get("having") or []),
            subqueries=list(meta.get("subqueries") or []),
        )

    @classmethod
    def from_components(
        cls,
        *,
        entity: str,
        fields: list[str],
        filters: dict[str, Any],
        **kwargs: Any,
    ) -> "QueryIR":
        joins = kwargs.get("joins")
        nested = kwargs.get("nested")
        aggregations = kwargs.get("aggregations")
        flat_filters, group_filters = _split_filters(filters, kwargs.get("exact_filter_keys"))
        ir_joins = [_join_from_dict(j) for j in (joins or []) if isinstance(j, dict)]
        ir_nested = [_nested_from_dict(n) for n in (nested or []) if isinstance(n, dict)]
        ir_aggs = [_agg_from_dict(a) for a in (aggregations or []) if isinstance(a, dict)]
        return cls(
            entity=entity,
            fields=list(fields),
            filters=flat_filters,
            joins=ir_joins,
            nested=ir_nested,
            aggregations=ir_aggs,
            group_filters=group_filters,
            order_by=kwargs.get("order_by"),
            order_dir=kwargs.get("order_dir"),
            limit=kwargs.get("limit"),
            offset=kwargs.get("offset"),
            target=kwargs.get("target", "graphql"),
            source_text=kwargs.get("source_text", ""),
            metadata=kwargs.get("metadata") or {},
            distinct=bool(kwargs.get("distinct", False)),
            having=list(kwargs.get("having") or []),
            subqueries=list(kwargs.get("subqueries") or []),
        )


class IRRenderer:
    def render(self, ir: QueryIR) -> str:
        raise NotImplementedError(f"{type(self).__name__} must implement render(ir: QueryIR) -> str")

    def render_many(self, irs: list[QueryIR]) -> list[str]:
        return [self.render(ir) for ir in irs]


def _split_filters(
    raw: dict[str, Any],
    exact_filter_keys: frozenset[str] | None = None,
) -> tuple[list[IRFilter], dict[str, Any]]:
    flat: list[IRFilter] = []
    groups: dict[str, Any] = {}
    exact_keys: frozenset[str] = exact_filter_keys or frozenset()

    suffix_op = {
        "_gte": "gte",
        "_lte": "lte",
        "_gt": "gt",
        "_lt": "lt",
        "_ne": "ne",
        "_in": "in",
        "_nin": "nin",
    }

    for key, value in raw.items():
        if key in {"and", "or", "not"} and isinstance(value, list):
            groups[key] = value
            continue
        flat.append(_build_ir_filter(key, value, exact_keys, suffix_op))

    return flat, groups


def _build_ir_filter(
    key: str,
    value: Any,
    exact_keys: frozenset[str],
    suffix_op: dict[str, str],
) -> IRFilter:
    if value is None:
        return IRFilter(key=key, value=None, operator="is_null")
    canonical_key, operator = _resolve_filter_operator(key, exact_keys, suffix_op)
    return IRFilter(key=canonical_key, value=value, operator=operator)


def _resolve_filter_operator(
    key: str,
    exact_keys: frozenset[str],
    suffix_op: dict[str, str],
) -> tuple[str, str]:
    if key in exact_keys:
        return key, "eq"
    for suffix, op in suffix_op.items():
        if key.endswith(suffix):
            return key[: -len(suffix)], op
    return key, "eq"


def _join_from_dict(d: dict[str, Any]) -> IRJoin:
    on_clause = d.get("on_clause", "")
    on_left, on_right = _parse_on_clause(on_clause)
    raw_filters = d.get("filters", {})
    flat_filters, _ = _split_filters(raw_filters if isinstance(raw_filters, dict) else {})
    return IRJoin(
        relation=str(d.get("relation", "")),
        target=str(d.get("target", "")),
        on_left=on_left,
        on_right=on_right,
        fields=list(d.get("fields") or []),
        filters=flat_filters,
        join_type=str(d.get("join_type", "LEFT")).upper(),
    )


def _nested_from_dict(d: dict[str, Any]) -> IRNested:
    raw_filters = d.get("filters", d.get("args", {}))
    flat_filters, _ = _split_filters(raw_filters if isinstance(raw_filters, dict) else {})
    children = [_nested_from_dict(child) for child in d.get("nested", []) if isinstance(child, dict)]
    return IRNested(
        relation=str(d.get("relation", d.get("name", ""))),
        target=str(d.get("target", d.get("entity", ""))),
        fields=list(d.get("fields") or []),
        filters=flat_filters,
        children=children,
    )


def _agg_from_dict(d: dict[str, Any]) -> IRAggregation:
    return IRAggregation(
        function=str(d.get("function", "COUNT")).upper(),
        field=str(d.get("field", "*")),
        alias=d.get("alias"),
    )


def _parse_on_clause(on_clause: str) -> tuple[str, str]:
    if "=" in on_clause:
        parts = on_clause.split("=", 1)
        return parts[0].strip(), parts[1].strip()
    return on_clause.strip(), ""
