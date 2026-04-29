"""Domain entities.

Contains core business models, enums, and data structures.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


# Query keys used for fetching DAX and cache access. (OO-004, CA-002, CA-004)
class QueryKey(StrEnum):
    """Enumeration of standard dashboard query keys."""

    SALES_BY_DATE = "sales_by_date"
    SALES_BY_CATEGORY = "sales_by_category"
    SALES_BY_TERRITORY = "sales_by_territory"
    TOP_N_PRODUCTS = "top_n_products"
    KPI_TOTALS = "kpi_totals"
    MODEL_SCHEMA = "model_schema"
    MODEL_RELATIONSHIPS = "model_relationships"


class FragmentCategory(StrEnum):
    """Enumeration of DAX fragment categories."""

    MEASURE = "measure"
    DIMENSION = "dimension"


class ColumnType(StrEnum):
    """Enumeration of semantic model column types."""

    REGULAR = "regular"
    KEY = "key"
    DATE = "date"
    MEASURE = "measure"
    HIDDEN = "hidden"


ThemeColor = Literal[
    "dark",
    "gray",
    "red",
    "pink",
    "grape",
    "violet",
    "indigo",
    "blue",
    "cyan",
    "teal",
    "green",
    "lime",
    "yellow",
    "orange",
]


@dataclass(frozen=True)
class KpiConfig:
    """Configuration for a KPI card."""

    label: str
    column: str
    formatter: Callable[[float | int], str]
    icon: str = ""
    color: ThemeColor = "blue"


@dataclass(frozen=True)
class ModelRelationship:
    """Represents a relationship between two tables in the semantic model."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    is_active: bool
    cross_filtering_behavior: str
    from_cardinality: str
    to_cardinality: str


@dataclass(frozen=True)
class LoadResult:
    """Result of a data loading operation."""

    success: bool
    loaded_keys: list[QueryKey]
    errors: dict[str, str]


@dataclass(frozen=True)
class TableSchema:
    """Schema for a single table in the semantic model."""

    name: str
    columns: list[str]
    measures: list[str]


@dataclass(frozen=True)
class ModelSchema:
    """Complete schema for the Power BI semantic model."""

    tables: dict[str, TableSchema]

    @property
    def table_names(self) -> list[str]:
        """Return list of all table names."""
        return list(self.tables.keys())
