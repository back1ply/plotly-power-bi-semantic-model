"""Tests for infrastructure/dax.py and application/data_loader.py."""

import pytest
import pandas as pd
from unittest.mock import MagicMock
from domain import QueryKey
from infrastructure.cache import QueryCache
from application.data_loader import StartupDataLoader


def test_startup_data_loader_populates_all_keys(mock_cache):
    """All QueryKey members are written after StartupDataLoader.populate_cache()."""
    mock_repo = MagicMock()
    mock_repo.refresh.return_value = pd.DataFrame([{"Revenue": 100.0}])
    
    data_loader = StartupDataLoader(mock_repo)

    result = data_loader.populate_cache(max_attempts=1)
    assert result.success

    assert mock_repo.refresh.call_count == len(QueryKey)


def test_data_loader_tolerates_query_error(mock_cache):
    """StartupDataLoader does not raise when a query throws an exception."""
    mock_repo = MagicMock()
    mock_repo.refresh.side_effect = Exception("PBI unavailable")

    data_loader = StartupDataLoader(mock_repo)

    result = data_loader.populate_cache(max_attempts=1)  # must not raise
    assert not result.success
    assert len(result.errors) > 0


def test_data_loader_tolerates_empty_result(mock_cache):
    """StartupDataLoader handles empty results gracefully."""
    mock_repo = MagicMock()
    mock_repo.refresh.return_value = pd.DataFrame()

    data_loader = StartupDataLoader(mock_repo)

    result = data_loader.populate_cache(max_attempts=1)  # must not raise
    assert not result.success
    assert len(result.errors) > 0


def test_cache_set_and_get(mock_cache):
    """QueryCache set and get work as expected."""
    query_cache = QueryCache(cache_dir=mock_cache.directory)
    data = [{"val": 1}, {"val": 2}, {"val": 3}]
    
    query_cache.set(QueryKey.KPI_TOTALS, data)
    result = query_cache.get(QueryKey.KPI_TOTALS)
    
    assert result is not None
    assert result == data


def test_cache_returns_none_for_missing_key(mock_cache):
    """QueryCache returns None for missing keys."""
    query_cache = QueryCache(cache_dir=mock_cache.directory)
    assert query_cache.get(QueryKey.SALES_BY_DATE) is None
