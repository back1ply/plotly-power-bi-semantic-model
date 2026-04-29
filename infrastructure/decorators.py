"""Infrastructure Decorators.

Contains decorators for infrastructure components, such as repository caching.
"""

import hashlib
import json
import logging
import random
import time
from collections.abc import Callable
from typing import Any
from typing import ParamSpec
from typing import TypeVar

import pandas as pd

from domain import FragmentCategory
from domain import ModelRelationship
from domain import ModelSchema
from domain import QueryError
from domain import QueryKey
from domain import ReadWriteCachePort
from domain import RepositoryPort
from domain.utils import with_retry

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class CachingRepositoryDecorator(RepositoryPort):
    """Decorator that adds caching to a RepositoryPort. (OO-003, CA-001)"""

    def __init__(
        self,
        repository: RepositoryPort,
        query_cache: ReadWriteCachePort,
    ) -> None:
        """Initialize decorator with an inner repository and cache.

        Args:
            repository: The inner repository to decorate.
            query_cache: The cache to retrieve/store data.
        """
        self._repository = repository
        self._cache = query_cache

    def _get_dynamic_key(
        self, key: str, limit: int | None = None, **kwargs: Any
    ) -> str:
        """Generate a stable cache key for dynamic queries."""
        # Sort keys to ensure stable hashing
        param_data = {"kwargs": kwargs, "limit": limit}
        param_str = json.dumps(param_data, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()
        return f"dynamic:{key}:{param_hash}"

    def get_raw_query(self, key: QueryKey) -> str:
        """Delegate to inner repository."""
        return self._repository.get_raw_query(key)

    def get_query_template(self, key: str) -> str:
        """Delegate to inner repository."""
        return self._repository.get_query_template(key)

    def get_fragment(self, category: FragmentCategory, key: str) -> str:
        """Delegate to inner repository."""
        return self._repository.get_fragment(category, key)

    def get_formatted_query(self, key: str, **kwargs: Any) -> str:
        """Delegate to inner repository."""
        return self._repository.get_formatted_query(key, **kwargs)

    def get_data(self, key: QueryKey, limit: int | None = None) -> pd.DataFrame:
        """Check cache first, or fetch from inner repository if missing."""
        cache_key = f"{key.value}:limit:{limit}" if limit else key.value
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, pd.DataFrame):
            return data

        return self.refresh(key, limit)

    def query(self, dax: str) -> list[dict[str, Any]]:
        """Execute a raw DAX query (no caching). (CA-002)"""
        return self._repository.query(dax)

    def get_schema(self) -> ModelSchema:
        """Get the model schema, using cache if available."""
        # Use a special key for schema metadata
        cache_key = "schema_metadata"
        data = self._cache.get(cache_key)
        if data is not None:
            # Check if we got old dict format instead of dataclass (CA-001)
            if isinstance(data, ModelSchema):
                return data

            logger.warning("get_schema: cached data is not ModelSchema, refreshing")

        data = self._repository.get_schema()
        self._cache.set(cache_key, data)
        return data

    def get_relationships(self) -> list[ModelRelationship]:
        """Get the model relationships, using cache if available."""
        cache_key = "model_relationships"
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, list):
            return data

        data = self._repository.get_relationships()
        self._cache.set(cache_key, data)
        return data

    def get_dynamic_data(
        self,
        key: str,
        parameters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Fetch data using a dynamic query template and parameters (cached)."""
        cache_key = self._get_dynamic_key(key, parameters=parameters, limit=limit)
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, pd.DataFrame):
            return data

        data = self._repository.get_dynamic_data(
            key, parameters=parameters, limit=limit
        )
        self._cache.set(cache_key, data)
        return data

    def get_summarized_data(
        self, measure_key: str, dimension_key: str, limit: int | None = None
    ) -> pd.DataFrame:
        """Fetch summarized data for a specific measure and dimension (cached)."""
        cache_key = f"summarized:{measure_key}:{dimension_key}:limit:{limit}"
        data = self._cache.get(cache_key)
        if data is not None and isinstance(data, pd.DataFrame):
            return data

        data = self._repository.get_summarized_data(measure_key, dimension_key, limit)
        self._cache.set(cache_key, data)
        return data

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        """Delegate to inner repository."""
        return self._repository.get_summarized_query_text(measure_key, dimension_key)

    def refresh(self, key: QueryKey, limit: int | None = None) -> pd.DataFrame:
        """Fetch fresh data from inner repository and update cache."""
        data = self._repository.refresh(key, limit)
        cache_key = f"{key.value}:limit:{limit}" if limit else key.value
        self._cache.set(cache_key, data)
        return data
