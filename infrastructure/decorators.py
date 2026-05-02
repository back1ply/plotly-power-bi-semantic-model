"""Infrastructure Decorators.

Contains decorators for infrastructure components, such as repository caching.
"""

import hashlib
import json
import logging
from typing import Any

from domain import CacheKey
from domain import DataAnalysisExpressionsFragment
from domain import DataAnalysisExpressionsSourcePort
from domain import DataAnalysisExpressionsTemplate
from domain import DataFrame
from domain import DataPort
from domain import FragmentCategory
from domain import ModelRelationship
from domain import ModelSchema
from domain import QueryClientPort
from domain import QueryKey
from domain import ReadWriteCachePort
from domain import RepositoryPort
from domain import SchemaPort

logger = logging.getLogger(__name__)


class CachingSchemaDecorator(SchemaPort):
    """Decorator that adds caching to a SchemaPort. (OO-002, CA-001)"""

    def __init__(
        self,
        schema_service: SchemaPort,
        query_cache: ReadWriteCachePort,
    ) -> None:
        """Initialize decorator with an inner service and cache."""
        self._service = schema_service
        self._cache = query_cache

    def get_schema(self) -> ModelSchema:
        """Get the model schema, using cache if available."""
        cache_key = CacheKey.SCHEMA_METADATA
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, ModelSchema):
            return data

        data = self._service.get_schema()
        self._cache.set(cache_key, data)
        return data

    def get_relationships(self) -> list[ModelRelationship]:
        """Get the model relationships, using cache if available."""
        cache_key = CacheKey.MODEL_RELATIONSHIPS
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, list):
            return data

        data = self._service.get_relationships()
        self._cache.set(cache_key, data)
        return data


class CachingDataDecorator(DataPort):
    """Decorator that adds caching to a DataPort. (OO-002, CA-001)"""

    def __init__(
        self,
        data_service: DataPort,
        query_cache: ReadWriteCachePort,
    ) -> None:
        """Initialize decorator with an inner service and cache."""
        self._service = data_service
        self._cache = query_cache

    def _get_dynamic_key(
        self, key: str, parameters: dict[str, Any] | None = None, limit: int | None = None
    ) -> str:
        """Generate a stable cache key for dynamic queries. (API-005)"""
        # Sort keys to ensure stable hashing
        param_data = {"parameters": parameters, "limit": limit}
        param_str = json.dumps(param_data, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()
        return f"dynamic:{key}:{param_hash}"

    def get_data(self, key: QueryKey, limit: int | None = None) -> DataFrame:
        """Check cache first, or fetch from inner service if missing."""
        cache_key = f"{key.value}:limit:{limit}" if limit else key.value
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, DataFrame):
            return data

        return self.fetch_fresh_data(key, limit)

    def get_dynamic_data(
        self,
        key: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> DataFrame:
        """Fetch data using a dynamic query template and parameters (cached)."""
        cache_key = self._get_dynamic_key(key, parameters=parameters, limit=limit)
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, DataFrame):
            return data

        data = self._service.get_dynamic_data(key, parameters=parameters, limit=limit)
        self._cache.set(cache_key, data)
        return data

    def get_summarized_data(
        self, measure_key: str, dimension_key: str, limit: int | None = None
    ) -> DataFrame:
        """Fetch summarized data for a specific measure and dimension (cached)."""
        cache_key = f"summarized:{measure_key}:{dimension_key}:limit:{limit}"
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, DataFrame):
            return data

        data = self._service.get_summarized_data(measure_key, dimension_key, limit)
        self._cache.set(cache_key, data)
        return data

    def fetch_fresh_data(self, key: QueryKey, limit: int | None = None) -> DataFrame:
        """Fetch fresh data from inner service and update cache."""
        data = self._service.fetch_fresh_data(key, limit)
        cache_key = f"{key.value}:limit:{limit}" if limit else key.value
        self._cache.set(cache_key, data)
        return data


class UnifiedCachingRepository(RepositoryPort):
    """Composite decorator that maintains the RepositoryPort interface. (CA-001)

    Delegates to specialized caching decorators to satisfy the unified interface
    while adhering to the Interface Segregation Principle internally.
    """

    def __init__(
        self,
        schema: SchemaPort,
        data: DataPort,
        dax_query_source: DataAnalysisExpressionsSourcePort,
        client: QueryClientPort,  # For query()
    ) -> None:
        self._schema = schema
        self._data = data
        self._dax = dax_query_source
        self._client = client

    def get_schema(self) -> ModelSchema:
        return self._schema.get_schema()

    def get_relationships(self) -> list[ModelRelationship]:
        return self._schema.get_relationships()

    def get_data(self, key: QueryKey, limit: int | None = None) -> DataFrame:
        return self._data.get_data(key, limit)

    def get_dynamic_data(
        self,
        key: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> DataFrame:
        return self._data.get_dynamic_data(key, parameters=parameters, limit=limit)

    def get_summarized_data(
        self, measure_key: str, dimension_key: str, limit: int | None = None
    ) -> DataFrame:
        return self._data.get_summarized_data(measure_key, dimension_key, limit)

    def fetch_fresh_data(self, key: QueryKey, limit: int | None = None) -> DataFrame:
        return self._data.fetch_fresh_data(key, limit)

    def get_raw_query(self, key: QueryKey) -> str:
        return self._dax.get_raw_query(key)

    def get_query_template(self, key: str) -> DataAnalysisExpressionsTemplate:
        """Delegate to DataAnalysisExpressionsSourcePort. (OO-004)"""
        return self._dax.get_query_template(key)

    def get_fragment(self, category: FragmentCategory, key: str) -> DataAnalysisExpressionsFragment:
        """Delegate to DataAnalysisExpressionsSourcePort. (OO-004)"""
        return self._dax.get_fragment(category, key)

    def get_formatted_query(self, key: str, parameters: dict[str, Any] | None = None) -> str:
        return self._dax.get_formatted_query(key, parameters=parameters)

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        return self._dax.get_summarized_query_text(measure_key, dimension_key)

    def query(self, dax_query: str) -> DataFrame:
        return self._client.query(dax_query)
