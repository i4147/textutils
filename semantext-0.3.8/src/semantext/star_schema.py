from typing import Dict, List
from sqlglot import select
from sqlglot.expressions import column, to_identifier
from semantext.models import FactTable, DimTable, ChartProperties, ChartColumn
from semantext.utils import (
    generate_on_clause,
    format_columns,
    generate_cte,
    validate_inputs,
)
import uuid


@validate_inputs
def generate_sql(
    chart_properties: ChartProperties,
    fact_tables: List[FactTable],
    dim: DimTable,
    dialect: str,
):
    all_columns = {dim.name: {col.column_name: col for col in dim.columns}} | {
        curr_fact.name: {col.column_name: col for col in curr_fact.columns} for curr_fact in fact_tables
    }
    metric_cols = [
        format_columns(current_chart_attribute=curr_metric, all_columns=all_columns)
        for curr_metric in chart_properties.metrics
    ]
    dim_col = format_columns(current_chart_attribute=chart_properties.dimension, all_columns=all_columns)
    dim_display_col = format_columns(
        current_chart_attribute=chart_properties.dimension,
        all_columns=all_columns,
        is_display=True,
    )
    where_col = (
        {
            curr_filter.table_name: {
                curr_filter.column_name: format_columns(current_chart_attribute=curr_filter, all_columns=all_columns)
            }
            for curr_filter in chart_properties.filters
        }
        if chart_properties.filters is not None
        else {}
    )
    base_cte_uuid = str(uuid.uuid4())
    base_cte = (
        select(*[dim_col.encode_select(), dim_display_col.encode_select()])
        .distinct()
        .from_(dim_col.encode_table())
        .where(
            *[col.encode_where() for col in where_col[dim_col.table_name].values()] if chart_properties.filters else []
        )
    )
    query = select().with_(alias=to_identifier(base_cte_uuid, quoted=True), as_=base_cte)
    dim_display_col.table_name = base_cte_uuid
    dim_col.table_name = base_cte_uuid
    metric_cols_by_table: Dict[str, List[ChartColumn]] = {}
    for curr_col in metric_cols:
        if curr_col.table_name in metric_cols_by_table.keys():
            metric_cols_by_table[curr_col.table_name].append(curr_col)
        else:
            metric_cols_by_table[curr_col.table_name] = [curr_col]
    tables_uuid: Dict[str, str] = {}
    join_col = {}
    for curr_table, curr_cols in metric_cols_by_table.items():
        tables_uuid[curr_table] = str(uuid.uuid4())
        curr_table_dim = [
            dimension
            for fact_table in fact_tables
            for dimension in fact_table.dimensions
            if dimension.table_name == dim.name and fact_table.name == curr_table
        ][0]
        curr_table_join_col = all_columns[curr_table][curr_table_dim.fact_dim_key]
        curr_table_dim_join_col = all_columns[dim.name][curr_table_dim.dim_key]
        curr_table_dim_join_col = ChartColumn(**curr_table_dim_join_col.dump_exclude(), table_name=dim.name)
        if curr_table_dim_join_col.column_name != dim_col.column_name:
            query.ctes[0].selects.append(*[curr_table_dim_join_col.encode_select()])
            base_cte = base_cte.select(*[curr_table_dim_join_col.encode_select()])
        curr_table_dim_join_col.table_name = base_cte_uuid
        curr_cte = generate_cte(
            select_cols=curr_cols,
            fact_join_col=ChartColumn(**curr_table_join_col.dump_exclude(), table_name=curr_table),
            dim_join_col=curr_table_dim_join_col,
            group_by_cols=[curr_table_dim_join_col],
            where_cols=list(where_col.get(curr_table, {}).values()),
            alias=tables_uuid[curr_table],
        )
        join_col[tables_uuid[curr_table]] = [
            ChartColumn(**curr_table_join_col.dump_exclude(), table_name=tables_uuid[curr_table]),
            curr_table_dim_join_col,
        ]
        query = query.with_(
            alias=to_identifier(curr_cte.alias, quoted=True),
            as_=curr_cte.this,
        )
    ctes_without_base = [cte for cte in query.ctes if cte.alias != base_cte_uuid]
    query = query.select(*[dim_col.encode_select(), dim_display_col.encode_select()]).from_(
        to_identifier(base_cte_uuid, quoted=True)
    )
    for curr_cte in ctes_without_base:
        query = query.select(*[
            column(table=curr_cte.alias, col=col.alias, quoted=True)
            for col in curr_cte.selects
            if col.alias != dim_col.column_name
            and col.alias not in [col.column_name for col in join_col[curr_cte.alias]]
        ]).join(
            to_identifier(curr_cte.alias, quoted=True),
            join_type="left",
            on=generate_on_clause(
                source_col=join_col[curr_cte.alias][0],
                dest_col=join_col[curr_cte.alias][1],
            ),
        )
    return query.sql(pretty=True, dialect=dialect)


if __name__ == "__main__":
    from pathlib import Path
    import json

    dims = []
    fact = []
    chart_prop = []
    p = Path("./json_examples")
    for curr_file in p.iterdir():
        if "dim" in curr_file.name:
            dims.append(DimTable(**json.loads(curr_file.read_text("utf-8"))))
        elif "fact" in curr_file.name:
            fact.append(FactTable(**json.loads(curr_file.read_text("utf-8"))))
        else:
            chart_prop.append(ChartProperties(**json.loads(curr_file.read_text("utf-8"))))
    a = generate_sql(chart_prop[0], fact, dims[0], dialect="trino")
    print(a)
    with open("test.sql", "w") as f:
        f.write(a)
