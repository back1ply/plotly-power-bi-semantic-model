"""Tests for infrastructure/dax.py — JSON loader and get_startup_query."""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from domain import QueryKey, QueryNotFoundError
from infrastructure.dax import DaxQueryLoader


class TestFetchStartupQuery:
    def test_returns_query_for_valid_key(self):
        """get_raw_query returns the DAX string from dax.json."""
        dax_path = Path(__file__).resolve().parent.parent / "queries" / "dax.json"
        loader = DaxQueryLoader.from_path(dax_path)
        dax = loader.get_raw_query(QueryKey.KPI_TOTALS)
        assert isinstance(dax, str)
        assert "EVALUATE" in dax.upper()

    def test_raises_keyerror_for_unknown_key(self):
        """get_raw_query raises QueryNotFoundError for invalid keys."""
        dax_path = Path(__file__).resolve().parent.parent / "queries" / "dax.json"
        loader = DaxQueryLoader.from_path(dax_path)
        with pytest.raises(QueryNotFoundError):
            loader.get_raw_query("invalid_key")

    def test_error_message_lists_available_keys(self):
        """QueryNotFoundError message includes the available keys."""
        dax_path = Path(__file__).resolve().parent.parent / "queries" / "dax.json"
        loader = DaxQueryLoader.from_path(dax_path)
        with pytest.raises(QueryNotFoundError) as excinfo:
            loader.get_raw_query("no_such_key")
        assert "Available:" in str(excinfo.value)


class TestDaxCache:
    def test_json_loaded_and_cached(self):
        """DaxQueryLoader loads and stores data."""
        dax_path = Path(__file__).resolve().parent.parent / "queries" / "dax.json"
        loader = DaxQueryLoader.from_path(dax_path)
        loader.get_raw_query(QueryKey.KPI_TOTALS) # Trigger load
        assert loader._loaded is True
        assert len(loader._startup) > 0
        assert QueryKey.KPI_TOTALS in loader._startup
        assert "summarizecolumns" in loader._dynamic


class TestAllCacheKeysHaveQueries:
    def test_every_cache_key_has_a_startup_query(self):
        """Each key in QueryKey maps to a non-empty DAX string in dax.json."""
        dax_path = Path(__file__).resolve().parent.parent / "queries" / "dax.json"
        loader = DaxQueryLoader.from_path(dax_path)
        for key in QueryKey:
            dax = loader.get_raw_query(key)
            assert isinstance(dax, str), f"DAX for '{key}' is not a string"
            assert len(dax.strip()) > 0, f"DAX for '{key}' is empty"
            assert "EVALUATE" in dax.upper(), (
                f"DAX for '{key}' missing EVALUATE keyword"
            )
