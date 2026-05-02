"""Caching implementations for Power BI query results.

Provides disk-based caching using Arrow IPC for zero-copy DataFrame storage
and standard diskcache for other objects.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import diskcache
import polars as pl

from domain import DataFrame
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

    def evict(self, key: str) -> None:
        """Remove a specific key from the cache."""
        if key in self._store:
            del self._store[key]


class QueryCache(ReadWriteCachePort):
    """Hybrid disk cache using Arrow IPC for DataFrames and DiskCache for others.

    Implements domain.ReadWriteCachePort.
    """

    def __init__(
        self,
        cache_dir: str,
        ttl_seconds: int = 3600,
    ) -> None:
        """Initialize cache parameters.

        Args:
            cache_dir: Path to cache directory.
            ttl_seconds: Cache TTL in seconds.
        """
        self._cache_dir = Path(cache_dir)
        self._ipc_dir = self._cache_dir / "ipc"
        self._ttl = ttl_seconds
        self._cache_instance: diskcache.Cache | None = None

        # Ensure IPC directory exists
        self._ipc_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _cache(self) -> diskcache.Cache:
        """Lazy initialization for diskcache.Cache."""
        if self._cache_instance is None:
            self._cache_instance = diskcache.Cache(str(self._cache_dir), expire=self._ttl)
        return self._cache_instance

    def _get_ipc_path(self, key: str) -> Path:
        """Generate a filesystem path for an Arrow IPC file based on key."""
        # Sanitize key for filename
        safe_key = "".join([c if c.isalnum() else "_" for c in key])
        return self._ipc_dir / f"{safe_key}.arrow"

    def set(self, key: str, value: Any) -> None:
        """Store value in cache, using Arrow IPC for DataFrames."""
        if isinstance(value, DataFrame):
            ipc_path = self._get_ipc_path(key)
            try:
                # Write to native Arrow IPC format for zero-copy reads
                value.write_ipc(ipc_path)
                # Store a sentinel in diskcache to manage TTL and tracking
                self._cache.set(key, f"__SENTINEL_IPC__:{ipc_path}")
                return
            except Exception as exception:
                logger.error("Failed to write Arrow IPC for key %s: %s", key, exception)
                # Fallback to standard diskcache (Pickle) if IPC fails
                pass

        self._cache.set(key, value)

    def get(self, key: str) -> Any | None:
        """Retrieve value from cache, handling Arrow IPC sentinels."""
        data = self._cache.get(key)

        if isinstance(data, str) and data.startswith("__SENTINEL_IPC__:"):
            ipc_path = Path(data.split(":", 1)[1])
            if ipc_path.exists():
                try:
                    # Memory-map the file for zero-copy performance
                    return pl.read_ipc(ipc_path, memory_map=True)
                except Exception as exception:
                    logger.error("Failed to read Arrow IPC for key %s: %s", key, exception)
                    # If reading IPC fails, treat as miss
                    return None
            return None

        return data
