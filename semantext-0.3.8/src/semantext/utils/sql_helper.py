from typing import Dict, List, Literal
from sqlglot import select, to_identifier
from sqlglot.expressions import EQ, Column, Condition, column, condition, CTE
from semantext.models import (
    ChartColumn,
    ChartProperties,
    FactTable,
    DimTable,
    Dimension,
    Metric,
    TableColumn,
    Filter,
)


def generate_on_clause(source_col: ChartColumn, dest_col: ChartColumn) -> EQ:
    return source_col.encode_on().eq(dest_col.encode_on())


def format_columns(
    current_chart_attribute: Dimension | Metric | Filter,
    all_columns: Dict[str, Dict[str, TableColumn]],
    is_display: bool = False,
) -> ChartColumn:
    col = all_columns[current_chart_attribute.table_name][current_chart_attribute.column_name]
    if isinstance(current_chart_attribute, Dimension):
        if is_display:
            col = all_columns[current_chart_attribute.table_name][current_chart_attribute.column_name_display]
        return ChartColumn(**col.dump_exclude(), table_name=current_chart_attribute.table_name)
    elif isinstance(current_chart_attribute, Metric):
        return ChartColumn(
            **col.dump_exclude(),
            table_name=current_chart_attribute.table_name,
            expression=current_chart_attribute.expression,
        )
    elif isinstance(current_chart_attribute, Filter):
        return ChartColumn(
            **col.dump_exclude(),
            operation=current_chart_attribute.operation,
            where_value=current_chart_attribute.value,
            table_name=current_chart_attribute.table_name,
        )
    raise ValueError("Invalid chart attribute type")


def generate_cte(
    select_cols: List[ChartColumn],
    fact_join_col: ChartColumn,
    dim_join_col: ChartColumn,
    alias: str,
    group_by_cols: List[ChartColumn],
    where_cols: List[ChartColumn] = [],
    join_type: Literal["inner", "left", "right", "full"] = "inner",
) -> CTE:
    return CTE(
        this=select(*[col.encode_select() for col in select_cols + group_by_cols])
        .from_((fact_join_col.encode_table()))
        .join(
            (dim_join_col.encode_table()),
            on=generate_on_clause(
                dim_join_col,
                fact_join_col,
            ),
            join_type=join_type,
        )
        .group_by(*[col.encode_group() for col in group_by_cols])
        .where(*[col.encode_where() for col in where_cols]),
        alias=to_identifier(name=alias, quoted=True),
    )
