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

    TREND_DATA = "sales_trend_data"
    CATEGORY_DATA = "category_sales_data"
    CATEGORY_TREND_DATA = "category_trend_data"
    TERRITORY_DATA = "territory_sales_data"
    TERRITORY_PROFITABILITY_DATA = "territory_profitability_data"
    TOP_N_DATA = "top_products_data"
    PROFITABILITY_DATA = "profitability_data"
    RESELLER_LEADERBOARD_DATA = "reseller_leaderboard_data"
    KEY_PERFORMANCE_INDICATOR_TOTALS = "key_performance_indicator_totals"
    MODEL_SCHEMA = "semantic_model_schema"
    MODEL_RELATIONSHIPS = "semantic_model_relationships"


class CacheKey(StrEnum):
    """Enumeration of standard cache keys. (OO-002)"""

    SCHEMA_METADATA = "schema_metadata"
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
class KeyPerformanceIndicatorConfig:
    """Configuration for a Key Performance Indicator card."""

    label: str
    column: str
    formatter: Callable[[float | int], str]
    icon: str = ""
    color: ThemeColor = "blue"
    delta_column: str = ""


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
class EmbedConfig:
    """Configuration for Power BI report embedding. (API-002)"""

    report_id: str
    embed_url: str
    access_token: str


@dataclass(frozen=True)
class DataAnalysisExpressionsFragment:
    """Represents a Data Analysis Expressions code fragment (e.g., a measure or dimension expression). (OO-004)"""

    content: str
    category: FragmentCategory
    key: str


@dataclass(frozen=True)
class DataAnalysisExpressionsTemplate:
    """Represents a formattable Data Analysis Expressions query template. (OO-004)"""

    content: str
    key: str


@dataclass(frozen=True)
class ModelSchema:
    """Complete schema for the Power BI semantic model."""

    tables: dict[str, TableSchema]

    @property
    def table_names(self) -> list[str]:
        """Return list of all table names."""
        return list(self.tables.keys())
