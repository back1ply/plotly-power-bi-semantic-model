"""Tests for core infrastructure internals."""

import polars as pl
import pytest
from unittest.mock import MagicMock
from infrastructure.cache import InMemoryCache, QueryCache
from infrastructure.data_analysis_expressions import DataAnalysisExpressionsQueryLoader
from domain import QueryKey, FragmentCategory, QueryNotFoundError

class TestInfraInternals:
    def test_in_memory_cache_eviction(self):
        """Verify manual eviction in InMemoryCache."""
        cache = InMemoryCache()
        cache.set("key1", "val1")
        assert cache.get("key1") == "val1"
        cache.evict("key1")
        assert cache.get("key1") is None

    def test_query_cache_ipc_roundtrip(self, tmp_path):
        """Verify Arrow IPC roundtrip for DataFrames in QueryCache."""
        cache_dir = str(tmp_path / ".cache")
        cache = QueryCache(cache_dir=cache_dir)
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        
        cache.set(QueryKey.TREND_DATA, df)
        result = cache.get(QueryKey.TREND_DATA)
        
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df)

    def test_dax_loader_missing_file_raises_error(self, tmp_path):
        """Verify that loader handles non-existent file path gracefully."""
        bad_path = tmp_path / "non_existent.json"
        loader = DataAnalysisExpressionsQueryLoader(bad_path)
        # Loader raises QueryNotFoundError (mapped from Exception) if file doesn't exist during load
        with pytest.raises(QueryNotFoundError):
            loader.get_raw_query(QueryKey.TREND_DATA)

    def test_dax_loader_fragment_logic(self, tmp_path):
        """Verify fragment retrieval and validation."""
        dax_file = tmp_path / "dax.json"
        dax_file.write_text('{"fragments": {"measure": {"Rev": "[Revenue]"}, "dimension": {}}, "startup": {}, "dynamic": {}}')
        
        loader = DataAnalysisExpressionsQueryLoader(dax_file)
        frag = loader.get_fragment(FragmentCategory.MEASURE, "Rev")
        assert frag.content == "[Revenue]"
        
        with pytest.raises(QueryNotFoundError):
            loader.get_fragment(FragmentCategory.MEASURE, "Missing")

    def test_unified_repository_proxy_methods(self):
        """Verify UnifiedCachingRepository correctly proxies non-cached methods."""
        mock_dax = MagicMock()
        mock_dax.get_query_template.return_value = "template"
        
        from infrastructure.decorators import UnifiedCachingRepository
        # Requires 4 args: schema, data, dax_query_source, client
        repo = UnifiedCachingRepository(MagicMock(), MagicMock(), mock_dax, MagicMock())
        
        result = repo.get_query_template("key")
        assert result == "template"
        mock_dax.get_query_template.assert_called_once_with("key")
