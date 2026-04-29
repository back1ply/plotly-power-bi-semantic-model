"""Caching implementations for Power BI query results.

Provides both disk-based and in-memory caching with TTL support.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

import diskcache

from domain import ReadWriteCachePort

logger = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    """Internal entry for in-memory cache with expiration."""

    value: Any
    expiry: float


class InMemoryCache(ReadWriteCachePort):
    """Session-based in-memory cache.

    Data is lost when the application process terminates.
    Ideal for avoiding stale metadata and file locking issues.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}

    def set(self, key: str, value: Any) -> None:
        """Store value in memory with expiry."""
        self._store[key] = _CacheEntry(value=value, expiry=time.time() + self._ttl)

    def get(self, key: str) -> Any | None:
        """Retrieve value if not expired."""
        entry = self._store.get(key)
        if not entry:
            return None

        if time.time() > entry.expiry:
            del self._store[key]
            return None

        return entry.value


class QueryCache(ReadWriteCachePort):
    """Encapsulates diskcache state and operations for DAX queries.

    Implements domain.ReadWriteCachePort.
    """

    def __init__(
        self,
        cache_dir: str,
        ttl_seconds: int = 3600,
    ) -> None:
        """Initialize cache parameters. (OO-005)

        Args:
            cache_dir: Path to cache directory.
            ttl_seconds: Cache TTL in seconds.
        """
        self._cache_dir = cache_dir
        self._ttl = ttl_seconds
        self._cache_instance: diskcache.Cache | None = None

    @property
    def _cache(self) -> diskcache.Cache:
        """Lazy initialization for diskcache.Cache."""
        if self._cache_instance is None:
            self._cache_instance = diskcache.Cache(self._cache_dir, expire=self._ttl)
        return self._cache_instance

    def set(self, key: str, value: Any) -> None:
        """Store value in cache."""
        self._cache.set(key, value)

    def get(self, key: str) -> Any | None:
        """Retrieve value from cache."""
        return self._cache.get(key)
