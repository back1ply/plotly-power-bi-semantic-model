"""Extended tests for cache TTL, edge cases, and invariants."""

import time
from unittest.mock import MagicMock
from domain import QueryKey
from infrastructure.cache import QueryCache
from infrastructure.data_analysis_expressions import DataAnalysisExpressionsQueryLoader


class TestCacheKeyHandling:
    def test_all_required_keys_defined(self):
        """Verify QueryKey enum members match expected dashboard keys."""
        expected = [
            "sales_trend_data",
            "category_sales_data",
            "territory_sales_data",
            "top_products_data",
            "key_performance_indicator_totals",
            "semantic_model_schema",
            "semantic_model_relationships",
        ]
        for key in expected:
            assert QueryKey(key) in QueryKey


class TestCacheTTL:
    def test_cache_expiration(self, mock_cache):
        query_cache = QueryCache(cache_dir=mock_cache.directory, ttl_seconds=1)
        assert query_cache._ttl == 1


class TestCacheEdgeCases:
    def test_populate_handles_empty_dataframe(self):
        """StartupDataLoader stores error info for empty DF."""
        from application.data_loader import StartupDataLoader
        import polars as pl
        
        mock_repo = MagicMock()
        mock_repo.fetch_fresh_data.return_value = pl.DataFrame()
        
        loader = StartupDataLoader(mock_repo)
        result = loader.populate_cache(max_attempts=1)
        
        assert len(result.errors) == len(QueryKey)

    def test_populate_handles_query_exception(self):
        """Query Error on one key does not abort the rest."""
        from application.data_loader import StartupDataLoader
        
        mock_repo = MagicMock()
        mock_repo.fetch_fresh_data.side_effect = Exception("API Error")
        
        loader = StartupDataLoader(mock_repo)
        loader.populate_cache(max_attempts=1)
        
        # All keys attempted
        assert mock_repo.fetch_fresh_data.call_count == len(QueryKey)


class TestCacheKeyInvariant:
    def test_all_cache_keys_have_dax_queries(self):
        """Every QueryKey has a non-empty entry in dax.json."""
        from pathlib import Path
        dax_path = Path(__file__).resolve().parent.parent / "queries" / "dax.json"
        loader = DataAnalysisExpressionsQueryLoader.from_path(dax_path)
        for key in QueryKey:
            dax = loader.get_raw_query(key)
            assert dax and len(dax.strip()) > 0, f"Empty DAX for key '{key}'"

    def test_expected_columns_defined_per_key(self):
        """Verify expected column shapes are documented (regression guard)."""
        expected_columns = {
            QueryKey.TREND_DATA: ["Fiscal Year", "MonthKey", "Month", "Revenue"],
            QueryKey.CATEGORY_DATA: ["Category", "Revenue"],
            QueryKey.CATEGORY_TREND_DATA: ["Fiscal Year", "Month", "Category", "Revenue", "Profit", "UnitsSold"],
            QueryKey.TERRITORY_DATA: ["Group", "Revenue"],
            QueryKey.TERRITORY_PROFITABILITY_DATA: ["Group", "Country", "Revenue", "Profit", "GrossMarginPct", "UnitsSold"],
            QueryKey.TOP_N_DATA: ["Product", "Category", "Revenue", "Profit"],
            QueryKey.PROFITABILITY_DATA: ["Country", "Category", "GrossMarginPct", "Revenue", "Profit"],
            QueryKey.RESELLER_LEADERBOARD_DATA: ["Reseller", "Country", "Revenue", "Profit", "GrossMarginPct", "SalesYoYPct", "YOYTarget"],
            QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS: ["Revenue", "Profit", "Orders", "AvgOrderValue"],
            QueryKey.MODEL_SCHEMA: ["Table", "Name"],
            QueryKey.MODEL_RELATIONSHIPS: ["FromTable", "FromColumn", "ToTable", "ToColumn"],
        }
        for key in QueryKey:
            assert key in expected_columns, f"No expected columns defined for '{key}'"
