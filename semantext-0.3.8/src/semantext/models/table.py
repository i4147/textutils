from typing import Any, Dict, List, Literal
from pydantic import BaseModel, field_validator
from semantext.helper_models import SQLTypes


class TableColumn(BaseModel):
    column_name: str
    description: str
    data_type: SQLTypes
    primary_key: bool | None = None

    @field_validator("data_type", mode="before")
    @classmethod
    def validate_data_type(cls, value):
        if isinstance(value, str):
            try:
                return SQLTypes[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid data_type: {value}. Valid options are: {[e.name for e in SQLTypes]}")
        return value

    def dump_exclude(self) -> Dict[str, Any]:
        return self.model_dump(exclude={"primary_key"})


class FactTable(BaseModel):
    name: str
    description: str
    columns: List[TableColumn]
    dimensions: List[TableDimension]


class TableDimension(BaseModel):
    name: str
    table_name: str
    fact_dim_key: str
    dim_key: str
    join_type: Literal["inner", "left", "right", "full"] = "inner"

    @field_validator("join_type", mode="before")
    @classmethod
    def validate_join_type(cls, value):
        if isinstance(value, str):
            value_lower = value.lower()
            valid_types = ["inner", "left", "right", "full"]
            if value_lower in valid_types:
                return value_lower
            else:
                raise ValueError(f"Invalid join_type: {value}. Valid options are: {valid_types}")
        return value


class DimTable(BaseModel):
    name: str
    description: str
    columns: List[TableColumn]
    hierarchies: List[Hierarchy] | None = None


class Level(BaseModel):
    column_name: str


class Hierarchy(BaseModel):
    name: str
    type: Literal["recursive", "levels"]
    description: str
    column_name: str | None = None
    levels: List[Level] | None = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value):
        if isinstance(value, str):
            value_lower = value.lower()
            valid_types = ["recursive", "levels"]
            if value_lower in valid_types:
                return value_lower
            else:
                raise ValueError(f"Invalid type: {value}. Valid options are: {valid_types}")
        return value
