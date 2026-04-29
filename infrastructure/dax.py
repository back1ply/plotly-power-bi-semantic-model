"""DAX Query Loader.

Provides a single source of truth for loading DAX queries from JSON.
Implements lazy loading with on-demand file reading.

DAX queries are stored in queries/dax.json under the "startup" key.
This module provides functions to retrieve these queries by cache key.
"""

import json
import logging
from pathlib import Path

from domain import DaxLoaderPort
from domain import FragmentCategory
from domain import QueryKey
from domain import QueryNotFoundError

logger = logging.getLogger(__name__)


class DaxQueryLoader(DaxLoaderPort):
    """Loads DAX queries from JSON files."""

    def __init__(self, dax_path: Path) -> None:
        """Initialize loader with file path. No I/O performed here. (OO-005)

        Args:
            dax_path: Required path to dax.json.
        """
        self._path = dax_path
        self._startup: dict[str, str] = {}
        self._dynamic: dict[str, str] = {}
        self._fragments: dict[str, dict[str, str]] = {}
        self._loaded = False

    @classmethod
    def from_path(cls, dax_path: Path) -> "DaxQueryLoader":
        """Factory method to load DAX queries from a specific disk path.
        Instantiates the loader without immediate I/O.
        """
        return cls(dax_path)

    def _ensure_loaded(self) -> None:
        """Lazy load data from disk if not already loaded."""
        if self._loaded:
            return

        if not self._path.exists():
            logger.error("DAX file not found: %s", self._path)
            return

        try:
            with self._path.open(encoding="utf-8") as f:
                content = json.load(f)
                self._startup = content.get("startup", {})
                self._dynamic = content.get("dynamic", {})
                self._fragments = content.get("fragments", {})
                self._loaded = True
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load DAX from %s: %s", self._path, exc)

    def get_raw_query(self, key: QueryKey) -> str:
        """Get DAX query string for given key from startup queries."""
        self._ensure_loaded()
        if key not in self._startup:
            raise QueryNotFoundError(
                f"Unknown startup query key: {key!r}. Available: {list(self._startup)}"
            )
        return self._startup[key]

    def get_query_template(self, key: str) -> str:
        """Get formattable DAX query string for given key from dynamic queries."""
        self._ensure_loaded()
        if key not in self._dynamic:
            raise QueryNotFoundError(
                f"Unknown dynamic query key: {key!r}. Available: {list(self._dynamic)}"
            )
        return self._dynamic[key]

    def get_fragment(self, category: FragmentCategory, key: str) -> str:
        """Get a DAX fragment (e.g., measure or definition)."""
        self._ensure_loaded()
        cat = self._fragments.get(category.value, {})
        if key not in cat:
            raise QueryNotFoundError(f"Unknown fragment key: {key!r} in category {category!r}.")
        return cat[key]
