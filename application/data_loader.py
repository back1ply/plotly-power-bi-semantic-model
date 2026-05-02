"""Data Loader.

Provides orchestration for loading startup data from Power BI and caching it.
"""

import logging

from domain import DataFrame
from domain import DataPort
from domain import LoadResult
from domain import QueryError
from domain import QueryKey
from domain import with_retry

logger = logging.getLogger(__name__)


class StartupDataLoader:
    """Orchestrates loading DAX queries into the cache."""

    def __init__(
        self,
        repository: DataPort,
        preload_keys: list[QueryKey] | None = None,
    ) -> None:
        """Initialize data loader with repository. (OO-002)

        Args:
            repository: The repository to use for refreshing data.
            preload_keys: Optional list of keys to pre-load. Defaults to all QueryKey.
        """
        self._repository = repository
        self._preload_keys = preload_keys or list(QueryKey)

    def populate_cache(self, max_attempts: int = 3, base_delay: float = 2.0) -> LoadResult:
        """Populate cache with retry logic at the query level."""

        @with_retry(
            max_attempts=max_attempts,
            base_delay=base_delay,
            exceptions=(QueryError, ValueError),
        )
        def _load_with_retry(key: QueryKey) -> DataFrame:
            """Execute a single query with retry logic."""
            result = self._repository.fetch_fresh_data(key)
            # Polars uses is_empty() instead of empty
            if result.is_empty():
                raise ValueError(f"Empty result from Power BI for {key}")
            return result

        loaded_keys: list[QueryKey] = []
        errors: dict[str, str] = {}

        for key in self._preload_keys:
            try:
                result = _load_with_retry(key)
                loaded_keys.append(key)
                logger.info("cache: '%s' cached (%d rows)", key, len(result))
            except Exception as exc:
                logger.error("cache: '%s' failed after all attempts: %s", key, exc)
                errors[key] = str(exc)

        return LoadResult(
            success=len(errors) == 0,
            loaded_keys=loaded_keys,
            errors=errors,
        )
