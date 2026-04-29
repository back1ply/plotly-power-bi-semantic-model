"""Domain ports.

Contains protocols defining interfaces for infrastructure components.
"""

from typing import Any
from typing import Protocol
from typing import runtime_checkable
from typing import TypeVar

import pandas as pd

from .entities import FragmentCategory
from .entities import ModelRelationship
from .entities import ModelSchema
from .entities import QueryKey

T = TypeVar("T")


@runtime_checkable
class DaxLoaderPort(Protocol):
    """Protocol for retrieving raw DAX query strings and fragments from storage."""

    def get_raw_query(self, key: QueryKey) -> str: ...

    def get_query_template(self, key: str) -> str: ...

    def get_fragment(self, category: FragmentCategory, key: str) -> str: ...


@runtime_checkable
class ReadCachePort(Protocol[T]):
    """Protocol for read-only cache access."""

    def get(self, key: str) -> T | None: ...


@runtime_checkable
class ReadWriteCachePort(ReadCachePort[T], Protocol[T]):
    """Protocol for read/write cache access."""

    def set(self, key: str, value: T) -> None: ...


@runtime_checkable
class QueryClientPort(Protocol):
    """Protocol for executing queries."""

    def query(self, dax: str) -> list[dict[str, Any]]:
        """Execute DAX query and return results as a list of records."""
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

    def get_embed_config(self, report_id: str) -> dict[str, str]:
        """Return embed URL and token for a report.

        Returns:
            Dict with embedUrl, accessToken, and reportId.
        """
        ...


@runtime_checkable
class DataPort(Protocol):
    """Protocol for fetching data from the dashboard repository."""

    def get_data(self, key: QueryKey, limit: int | None = None) -> pd.DataFrame:
        """Get data for a given query key."""
        ...

    def get_dynamic_data(
        self,
        key: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Fetch data using a dynamic query template and parameters."""
        ...

    def get_summarized_data(
        self, measure_key: str, dimension_key: str, limit: int | None = None
    ) -> pd.DataFrame:
        """Fetch summarized data for a specific measure and dimension."""
        ...

    def refresh(self, key: QueryKey, limit: int | None = None) -> pd.DataFrame:
        """Fetch fresh data from source and update cache."""
        ...


@runtime_checkable
class DaxSourcePort(DaxLoaderPort, Protocol):
    """Protocol for retrieving DAX query strings and fragments."""

    def get_formatted_query(
        self, key: str, parameters: dict[str, Any] | None = None
    ) -> str:
        """Get a formatted DAX query from a template and parameters."""
        ...

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        """Get the formatted DAX query text for a specific measure and dimension."""
        ...


@runtime_checkable
class RepositoryPort(SchemaPort, DataPort, DaxSourcePort, Protocol):
    """Unified protocol for dashboard data access.
    
    WARNING: This is a 'Fat Interface' that aggregates multiple responsibilities.
    Clients should prefer depending on narrower ports (SchemaPort, DataPort, etc.)
    where possible to adhere to the Interface Segregation Principle.
    This unified port is primarily intended for use in the Composition Root (DI Container)
    and high-level orchestration services.
    """

    def query(self, dax: str) -> list[dict[str, Any]]:
        """Execute a raw DAX query."""
        ...
