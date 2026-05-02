"""Tests for infrastructure/dax.py and application/data_loader.py."""

import polars as pl
import pytest
from unittest.mock import MagicMock
from domain import QueryKey
from infrastructure.cache import QueryCache
from application.data_loader import StartupDataLoader


def test_startup_data_loader_populates_all_keys(mock_cache):
    """All QueryKey members are written after StartupDataLoader.populate_cache()."""
    mock_repo = MagicMock()
    mock_repo.fetch_fresh_data.return_value = pl.DataFrame([{"Revenue": 100.0}])

    data_loader = StartupDataLoader(mock_repo)
    result = data_loader.populate_cache(max_attempts=1)
    assert result.success

    assert mock_repo.fetch_fresh_data.call_count == len(QueryKey)


def test_data_loader_tolerates_query_error(mock_cache):
    """StartupDataLoader does not raise when a query throws an exception."""
    mock_repo = MagicMock()
    mock_repo.fetch_fresh_data.side_effect = Exception("PBI unavailable")

    data_loader = StartupDataLoader(mock_repo)

    result = data_loader.populate_cache(max_attempts=1)  # must not raise
    assert not result.success
    assert len(result.errors) > 0


def test_data_loader_tolerates_empty_result(mock_cache):
    """StartupDataLoader handles empty results gracefully."""
    mock_repo = MagicMock()
    mock_repo.fetch_fresh_data.return_value = pl.DataFrame()

    data_loader = StartupDataLoader(mock_repo)

    result = data_loader.populate_cache(max_attempts=1)  # must not raise
    assert not result.success
    assert len(result.errors) > 0


def test_cache_set_and_get(mock_cache):
    """QueryCache set and get work as expected."""
    query_cache = QueryCache(cache_dir=mock_cache.directory)
    data = [{"val": 1}, {"val": 2}, {"val": 3}]
    
    query_cache.set(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS, data)
    result = query_cache.get(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS)
    
    assert result is not None
    assert result == data


def test_cache_returns_none_for_missing_key(mock_cache):
    """QueryCache returns None for missing keys."""
    query_cache = QueryCache(cache_dir=mock_cache.directory)
    assert query_cache.get(QueryKey.TREND_DATA) is None
