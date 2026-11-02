from datetime import datetime, timedelta
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlglot.expressions import (
    Alias,
    Column,
    column,
    condition,
    table_,
    Table,
)
from semantext.helper_models import (
    SQLTypes,
    SQLExpressions,
    SQLOperations,
    SQLGlotTable,
)


class GlobalColumn(BaseModel):
    column_name: str = Field(..., description="the technical column name")
    table_name: str = Field(..., description="the table name")
    model_config = ConfigDict(title="A global column representation")


class Dimension(GlobalColumn):
    column_name_display: str = Field(..., description="the technical column name that will translate code to display")
    label: str = Field(..., description="the label for the x axis")
    hierarchy: bool = Field(False, description="is the value of the column a hierarchy")
    filters: List[Filter] | None = Field(None, description="Which filters should be applied on the x axis")
    model_config = ConfigDict(title="A dimension representation, the x axis of a chart")


class Metric(GlobalColumn):
    expression: SQLExpressions = Field(..., description="Which expression should be applied on column in the y axis")
    model_config = ConfigDict(title="A metric representation, the y axis of a chart")

    @field_validator("expression", mode="before")
    @classmethod
    def validate_expression(cls, value):
        if isinstance(value, str):
            try:
                return SQLExpressions[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid expression: {value}. Valid options are: {[e.name for e in SQLExpressions]}")
        return value


class ChartProperties(BaseModel):
    dimension: Dimension = Field(
        description="The dimension of the chart, should be only a dimension table, cant be a fact table"
    )
    metrics: List[Metric] = Field(
        description="The metrics of the chart, should contain a list of fact tables (can be 1 or more), should contain only fact tables. "
    )
    filters: List[Filter] | None = Field(..., description="Which filters should be applied to the chart globally")
    model_config = ConfigDict(title="The technical spec for generating sql query for a visual chart")


class Filter(GlobalColumn):
    value: int | str | datetime = Field(..., description="The value of which we should generate a filter")
    operation: SQLOperations = Field(
        ...,
        description="The Operation we need to conduct on the column that we filter on",
    )

    @field_validator("operation", mode="before")
    @classmethod
    def validate_operation(cls, value):
        if isinstance(value, str):
            try:
                return SQLOperations[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid operation: {value}. Valid options are: {[e.name for e in SQLOperations]}")
        return value


class ChartColumn(BaseModel):
    column_name: str
    data_type: SQLTypes
    table_name: str
    expression: SQLExpressions | None = None
    where_value: Literal["yesterday", "last week", "last month", "last year"] | datetime | str | int | None = None
    operation: SQLOperations | None = None

    @field_validator("data_type", mode="before")
    @classmethod
    def validate_data_type(cls, value):
        if isinstance(value, str):
            try:
                return SQLTypes[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid data_type: {value}. Valid options are: {[e.name for e in SQLTypes]}")
        return value

    @field_validator("expression", mode="before")
    @classmethod
    def validate_expression(cls, value):
        if isinstance(value, str) and value is not None:
            try:
                return SQLExpressions[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid expression: {value}. Valid options are: {[e.name for e in SQLExpressions]}")
        return value

    @field_validator("operation", mode="before")
    @classmethod
    def validate_operation(cls, value):
        if isinstance(value, str) and value is not None:
            try:
                return SQLOperations[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid operation: {value}. Valid options are: {[e.name for e in SQLOperations]}")
        return value

    def __eq__(self, value: object) -> bool:
        if isinstance(value, ChartColumn):
            return self.column_name == value.column_name
        return False

    def encode_select(self) -> Alias | Column:
        table = self.__get_table_name()
        if self.expression is None:
            return column(
                col=self.column_name,
                quoted=True,
                **table.model_dump(),
            ).as_(self.column_name, quoted=True)
        else:
            return self.expression.expression(
                column=column(col=self.column_name, quoted=True, **table.model_dump()),
            )

    def encode_on(self) -> Column:
        table = self.__get_table_name()
        if self.expression is None:
            return column(
                col=self.column_name,
                quoted=True,
                **table.model_dump(),
            )
        else:
            raise ValueError("Not Good")

    def encode_group(self) -> Column:
        table = self.__get_table_name()
        if self.expression is None:
            return column(
                col=self.column_name,
                quoted=True,
                **table.model_dump(),
            )
        else:
            raise ValueError("Not Good")

    def encode_where(self):
        if self.where_value is None or self.operation is None:
            raise ValueError("Both 'where_value' and 'operation' must be set to encode a where condition")
        conversion_dict = {r"week": datetime.now() - timedelta(days=7)}
        return condition(
            self.operation.expression(
                column=column(
                    self.column_name,
                    **self.__get_table_name().model_dump(),
                    quoted=True,
                ),
                right=self.data_type.expression(self.where_value),
            )
        )

    def encode_table(self) -> Table:
        table = self.__get_table_name()
        return table_(**table.model_dump(), quoted=True)

    def __get_table_name(self) -> SQLGlotTable:
        try:
            catalog, schema, table = self.table_name.split(".")
            return SQLGlotTable(catalog=catalog, db=schema, table=table)
        except ValueError:
            return SQLGlotTable(table=self.table_name)
