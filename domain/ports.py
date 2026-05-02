"""Domain ports.

Contains protocols defining interfaces for infrastructure components.
"""

from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Protocol
from typing import runtime_checkable
from typing import TypeVar

from .entities import ColumnType
# ... rest of entities imports
from .entities import DataAnalysisExpressionsFragment
from .entities import DataAnalysisExpressionsTemplate
from .entities import EmbedConfig
from .entities import FragmentCategory
from .entities import ModelRelationship
from .entities import ModelSchema
from .entities import QueryKey

PortType = TypeVar("PortType")


@runtime_checkable
class DataFrame(Protocol):
    """Minimalist protocol representing a data frame structure. (API-003)
    
    This protocol defines the minimum surface area required by the domain 
    and presentation layers, decoupling them from specific libraries like Polars.
    """

    @property
    def columns(self) -> list[str]:
        """Return a list of column names."""
        ...

    @property
    def schema(self) -> dict[str, Any]:
        """Return the schema of the DataFrame (column names and types)."""
        ...

    def to_dicts(self) -> list[dict[str, Any]]:
        """Convert the DataFrame to a list of dictionaries."""
        ...

    def select(self, *exprs: Any, **named_exprs: Any) -> "DataFrame":
        """Select a subset of columns."""
        ...

    def filter(self, *predicates: Any, **constraints: Any) -> "DataFrame":
        """Filter the DataFrame."""
        ...

    def sort(
        self,
        by: str | Any | list[str | Any],
        descending: bool | list[bool] = False,
    ) -> "DataFrame":
        """Sort the DataFrame."""
        ...

    def with_columns(self, *exprs: Any, **named_exprs: Any) -> "DataFrame":
        """Add or overwrite columns."""
        ...

    def head(self, n: int) -> "DataFrame":
        """Return the first n rows."""
        ...

    def iter_rows(self, named: bool = True) -> Iterable[Any]:
        """Iterate over rows as dictionaries (if named=True) or tuples."""
        ...

    def get_column(self, name: str) -> Any:
        """Return a single column as a list-like object."""
        ...

    def unique(self, subset: str | list[str] | None = None, maintain_order: bool = False) -> "DataFrame":
        """Return unique rows."""
        ...

    def group_by(self, by: str | list[str]) -> Any:
        """Group by columns and return a GroupBy object."""
        ...

    def aggregate(self, by: str | list[str], aggregations: dict[str, str]) -> "DataFrame":
        """Perform aggregations on grouped data.
        
        Args:
            by: Column(s) to group by.
            aggregations: Mapping of column names to aggregation functions (e.g., {'Revenue': 'sum'}).
        """
        ...

    def pivot(
        self,
        index: str | list[str],
        on: str | list[str],
        values: str | list[str],
        aggregate_function: str = "sum",
    ) -> "DataFrame":
        """Pivot the DataFrame."""
        ...

    def with_column_renamed(self, old: str, new: str) -> "DataFrame":
        """Rename a column."""
        ...

    def cast_date(self, column: str, alias: str) -> "DataFrame":
        """Cast a string column to date/datetime and alias it."""
        ...

    def format_date(self, column: str, alias: str, format: str) -> "DataFrame":
        """Format a date column to string and alias it."""
        ...

    def is_empty(self) -> bool:
        """Return True if the DataFrame has no rows."""
        ...

    def __len__(self) -> int:
        """Return the number of rows."""
        ...


@runtime_checkable
class ClassifierPort(Protocol):
    """Protocol for classifying model columns."""

    def detect_type(self, column_name: str, table_name: str) -> ColumnType:
        """Detect column type using a rule-based approach."""
        ...


@runtime_checkable
class DataAnalysisExpressionsLoaderPort(Protocol):
    """Protocol for retrieving raw DAX query strings and fragments from storage. (OO-004)"""

    def get_raw_query(self, key: QueryKey) -> str: ...

    def get_query_template(self, key: str) -> DataAnalysisExpressionsTemplate: ...

    def get_fragment(self, category: FragmentCategory, key: str) -> DataAnalysisExpressionsFragment: ...


@runtime_checkable
class ReadCachePort(Protocol[PortType]):
    """Protocol for read-only cache access."""

    def get(self, key: str) -> PortType | None: ...


@runtime_checkable
class ReadWriteCachePort(ReadCachePort[PortType], Protocol[PortType]):
    """Protocol for read/write cache access."""

    def set(self, key: str, value: PortType) -> None: ...


@runtime_checkable
class QueryClientPort(Protocol):
    """Protocol for executing queries."""

    def query(self, dax_query: str) -> DataFrame:
        """Execute DAX query and return results as a DataFrame."""
        ...

    @property
    def has_credentials(self) -> bool:
        """Check if client is configured with credentials."""
        ...


@runtime_checkable
class TokenProviderPort(Protocol):
    """Protocol for providing authentication tokens."""

    def get_token(self) -> str:
        """Acquire and return an access token."""
        ...

    @property
    def has_credentials(self) -> bool:
        """Check if provider is configured with credentials."""
        ...


@runtime_checkable
class TemplateLoaderPort(Protocol):
    """Protocol for loading HTML templates and other assets. (OO-002)"""

    def load_html_template(self, name: str) -> str:
        """Load an HTML template by name."""
        ...


@runtime_checkable
class RateLimiterPort(Protocol):
    """Protocol for enforcing rate limits."""

    def enforce_rate_limit(self) -> None:
        """Record a request and raise RateLimitError if limit exceeded."""
        ...


@runtime_checkable
class SchemaPort(Protocol):
    """Protocol for accessing model metadata and relationships."""

    def get_schema(self) -> ModelSchema:
        """Get the semantic model schema (Tables, Columns, Measures)."""
        ...

    def get_relationships(self) -> list[ModelRelationship]:
        """Get the semantic model relationships."""
        ...


@runtime_checkable
class EmbedPort(Protocol):
    """Protocol for Power BI report embedding services. (CA-001)"""

    def get_embed_config(self, report_id: str) -> EmbedConfig:
        """Return embed URL and token for a report.

        Returns:
            EmbedConfig with embed_url, access_token, and report_id.
        """
        ...


@runtime_checkable
class DataPort(Protocol):
    """Protocol for fetching data from the dashboard repository."""

    def get_data(self, key: QueryKey, limit: int | None = None) -> DataFrame:
        """Get data for a given query key."""
        ...

    def get_dynamic_data(
        self,
        key: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> DataFrame:
        """Fetch data using a dynamic query template and parameters."""
        ...

    def get_summarized_data(
        self, measure_key: str, dimension_key: str, limit: int | None = None
    ) -> DataFrame:
        """Fetch summarized data for a specific measure and dimension."""
        ...

    def fetch_fresh_data(self, key: QueryKey, limit: int | None = None) -> DataFrame:
        """Fetch fresh data from source and update cache."""
        ...


@runtime_checkable
class DataAnalysisExpressionsSourcePort(DataAnalysisExpressionsLoaderPort, Protocol):
    """Protocol for retrieving DAX query strings and fragments."""

    def get_formatted_query(self, key: str, parameters: dict[str, Any] | None = None) -> str:
        """Get a formatted DAX query from a template and parameters. (API-001)"""
        ...

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        """Get the formatted DAX query text for a specific measure and dimension. (API-001)"""
        ...


@runtime_checkable
class RepositoryPort(SchemaPort, DataPort, DataAnalysisExpressionsSourcePort, Protocol):
    """Unified aggregate protocol for dashboard data access. (OO-001, CA-002)

    WARNING: This is a 'Fat Interface' (ISP violation) that aggregates multiple 
    independent responsibilities. It is provided ONLY for convenience in the 
    Composition Root (DI Container).

    High-level services and presentation components MUST NOT depend on this 
    aggregate port directly. Instead, they should depend on the narrowest 
    possible interface (e.g., SchemaPort, DataPort, or DataAnalysisExpressionsSourcePort) 
    to maintain strict interface segregation and minimize coupling.
    """

    def query(self, dax_query: str) -> DataFrame:
        """Execute a raw DAX query."""
        ...
