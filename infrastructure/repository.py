"""Repository.

Provides a data abstraction layer for the dashboard, decoupling UI from caching mechanisms.
"""

import logging
from typing import Any

import pandas as pd

from domain import DaxSourcePort
from domain import FragmentCategory
from domain import ModelRelationship
from domain import ModelSchema
from domain import QueryClientPort
from domain import QueryError
from domain import QueryKey
from domain import QueryNotFoundError
from domain import RepositoryPort
from domain import SchemaPort

logger = logging.getLogger(__name__)


class LiveRepository(RepositoryPort):
    """Provides access to live dashboard data by orchestrating specialized services."""

    def __init__(
        self,
        query_service: DaxSourcePort,
        schema_service: SchemaPort,
        query_client: QueryClientPort,
    ) -> None:
        """Initialize repository with specialized services.

        Args:
            query_service: Service for DAX query logic.
            schema_service: Service for model metadata logic.
            query_client: Client for executing queries.
        """
        self._queries = query_service
        self._schema = schema_service
        self._client = query_client

    def get_raw_query(self, key: QueryKey) -> str:
        """Delegate to DaxSourcePort."""
        return self._queries.get_raw_query(key)

    def get_query_template(self, key: str) -> str:
        """Delegate to DaxSourcePort."""
        return self._queries.get_query_template(key)

    def get_fragment(self, category: FragmentCategory, key: str) -> str:
        """Delegate to DaxSourcePort."""
        return self._queries.get_fragment(category, key)

    def get_formatted_query(self, key: str, parameters: dict[str, Any] | None = None) -> str:
        """Delegate to DaxSourcePort."""
        return self._queries.get_formatted_query(key, parameters=parameters)

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        """Delegate to DaxSourcePort."""
        return self._queries.get_summarized_query_text(measure_key, dimension_key)

    def query(self, dax: str) -> list[dict[str, Any]]:
        """Delegate to QueryClientPort. (CA-002)"""
        return self._client.query(dax)

    def get_schema(self) -> ModelSchema:
        """Delegate to SchemaPort."""
        return self._schema.get_schema()

    def get_relationships(self) -> list[ModelRelationship]:
        """Delegate to SchemaPort."""
        return self._schema.get_relationships()

    def get_data(self, key: QueryKey, limit: int | None = None) -> pd.DataFrame:
        """Get data directly from live repository."""
        return self.refresh(key, limit)

    def _execute_query_with_error_handling(
        self, dax: str, operation_name: str, limit: int | None = None
    ) -> pd.DataFrame:
        try:
            data = self._client.query(dax)
            df = pd.DataFrame(data)
            return df.head(limit) if limit else df
        except QueryNotFoundError:
            raise
        except Exception as exc:
            logger.exception("LiveRepository.%s: failed", operation_name)
            raise QueryError(f"Failed to execute query for {operation_name}") from exc

    def get_dynamic_data(
        self,
        key: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Fetch data using a dynamic query template and parameters."""
        dax = self._queries.get_formatted_query(key, parameters=parameters)
        return self._execute_query_with_error_handling(dax, f"get_dynamic_data({key})", limit)

    def get_summarized_data(
        self, measure_key: str, dimension_key: str, limit: int | None = None
    ) -> pd.DataFrame:
        """Fetch summarized data for a specific measure and dimension."""
        dax = self._queries.get_summarized_query_text(measure_key, dimension_key)
        return self._execute_query_with_error_handling(
            dax, f"get_summarized_data({measure_key} by {dimension_key})", limit
        )

    def refresh(self, key: QueryKey, limit: int | None = None) -> pd.DataFrame:
        """Fetch fresh data from live source."""
        dax = self._queries.get_raw_query(key)
        return self._execute_query_with_error_handling(dax, f"refresh({key})", limit)
