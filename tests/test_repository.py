"""Tests for DashboardRepository."""

import pytest
import pandas as pd
from unittest.mock import MagicMock
from domain import QueryKey, ModelSchema, TableSchema, QueryError, QueryNotFoundError
from infrastructure.repository import LiveRepository
from infrastructure.decorators import CachingRepositoryDecorator


class TestRepositoryDecorator:
    def test_get_data_cache_hit(self):
        """Decorator returns data from cache if available."""
        mock_cache = MagicMock()
        expected_df = pd.DataFrame([{"val": 1}])
        mock_cache.get.return_value = expected_df
        mock_inner = MagicMock()

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_data(QueryKey.KPI_TOTALS)

        pd.testing.assert_frame_equal(result, expected_df)
        mock_cache.get.assert_called_once()
        mock_inner.refresh.assert_not_called()

    def test_get_data_cache_miss_success(self):
        """Decorator fetches from inner repository on cache miss and populates cache."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        mock_inner = MagicMock()
        expected_df = pd.DataFrame([{"val": 2}])
        mock_inner.refresh.return_value = expected_df

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_data(QueryKey.KPI_TOTALS)

        pd.testing.assert_frame_equal(result, expected_df)
        mock_cache.get.assert_called_once()
        mock_inner.refresh.assert_called_once_with(QueryKey.KPI_TOTALS, None)
        mock_cache.set.assert_called_once()

    def test_get_schema_cache_hit(self):
        """Decorator returns schema from cache if available."""
        mock_cache = MagicMock()
        schema = ModelSchema(tables={"Table": TableSchema(name="Table", columns=["Col"], measures=[])})
        mock_cache.get.return_value = schema
        mock_inner = MagicMock()

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_schema()

        assert result == schema
        mock_cache.get.assert_called_once_with("schema_metadata")
        mock_inner.get_schema.assert_not_called()

    def test_get_schema_cache_miss(self):
        """Decorator fetches from inner repository on cache miss and populates cache."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        mock_inner = MagicMock()
        schema = ModelSchema(tables={"T": TableSchema(name="T", columns=["A"], measures=[])})
        mock_inner.get_schema.return_value = schema

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_schema()

        assert result == schema
        mock_cache.get.assert_called_once_with("schema_metadata")
        mock_inner.get_schema.assert_called_once()
        mock_cache.set.assert_called_once_with("schema_metadata", schema)

    def test_get_schema_stale_cache_dict(self):
        """Decorator refreshes schema if cache contains an old-style dict."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = {"old_table": {"Columns": [], "Measures": []}}
        
        mock_inner = MagicMock()
        schema = ModelSchema(tables={"NewTable": TableSchema(name="NewTable", columns=["A"], measures=[])})
        mock_inner.get_schema.return_value = schema

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_schema()

        assert result == schema
        assert isinstance(result, ModelSchema)
        mock_cache.get.assert_called_once_with("schema_metadata")
        mock_inner.get_schema.assert_called_once()
        mock_cache.set.assert_called_once_with("schema_metadata", schema)

    def test_get_dynamic_data_cache_hit(self):
        """Decorator returns dynamic data from cache."""
        mock_cache = MagicMock()
        expected_df = pd.DataFrame([{"dynamic": 1}])
        mock_cache.get.return_value = expected_df
        mock_inner = MagicMock()

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_dynamic_data("template", parameters={"val": 1})

        pd.testing.assert_frame_equal(result, expected_df)
        mock_inner.get_dynamic_data.assert_not_called()

    def test_get_summarized_data_cache_miss(self):
        """Decorator fetches and caches summarized data."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_inner = MagicMock()
        expected_df = pd.DataFrame([{"sum": 100}])
        mock_inner.get_summarized_data.return_value = expected_df

        repo = CachingRepositoryDecorator(mock_inner, mock_cache)
        result = repo.get_summarized_data("Rev", "Cat")

        pd.testing.assert_frame_equal(result, expected_df)
        mock_cache.set.assert_called_once()


class TestLiveRepository:
    def test_get_dynamic_data_success(self):
        """Live repo formats and executes dynamic query."""
        mock_source = MagicMock()
        mock_source.get_formatted_query.return_value = "FORMATTED DAX"
        mock_client = MagicMock()
        mock_client.query.return_value = [{"res": 1}]
        mock_schema = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        result = repo.get_dynamic_data("temp", parameters={"param": 1})

        assert isinstance(result, pd.DataFrame)
        mock_source.get_formatted_query.assert_called_once_with("temp", parameters={"param": 1})
        mock_client.query.assert_called_once_with("FORMATTED DAX")

    def test_get_summarized_data_success(self):
        """Live repo fetches summarized data using query service."""
        mock_source = MagicMock()
        mock_source.get_summarized_query_text.return_value = "SUMMARIZE DAX"
        mock_client = MagicMock()
        mock_client.query.return_value = [{"sum": 2}]
        mock_schema = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        result = repo.get_summarized_data("M", "D")

        assert result.iloc[0]["sum"] == 2
        mock_source.get_summarized_query_text.assert_called_once_with("M", "D")

    def test_refresh_success(self):
        """Live repository fetches from source and executes query."""
        mock_source = MagicMock()
        mock_source.get_raw_query.return_value = "EVALUATE Table"
        
        mock_client = MagicMock()
        mock_client.query.return_value = [{"val": 3}]
        mock_schema = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        result = repo.refresh(QueryKey.KPI_TOTALS)

        expected_df = pd.DataFrame([{"val": 3}])
        pd.testing.assert_frame_equal(result, expected_df)
        mock_source.get_raw_query.assert_called_once_with(QueryKey.KPI_TOTALS)
        mock_client.query.assert_called_once_with("EVALUATE Table")

    def test_get_schema_success(self):
        """Live repository delegates schema fetching to schema service."""
        expected = ModelSchema(
            tables={
                "Date": TableSchema(name="Date", columns=["Year"], measures=[]),
                "Sales": TableSchema(name="Sales", columns=["Amount"], measures=["TotalSales"]),
            }
        )
        mock_schema = MagicMock()
        mock_schema.get_schema.return_value = expected
        
        mock_source = MagicMock()
        mock_client = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        schema = repo.get_schema()

        assert schema == expected
        mock_schema.get_schema.assert_called_once()

    def test_get_relationships_success(self):
        """Live repository delegates relationship fetching to schema service."""
        expected = [{"FromTable": "Sales", "ToTable": "Date"}]
        mock_schema = MagicMock()
        mock_schema.get_relationships.return_value = expected
        
        mock_source = MagicMock()
        mock_client = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        result = repo.get_relationships()

        assert result == expected
        mock_schema.get_relationships.assert_called_once()

    def test_refresh_failure_raises_query_error(self):
        """Live repository raises QueryError if live fetch fails."""
        mock_source = MagicMock()
        mock_source.get_raw_query.return_value = "EVALUATE Table"
        
        mock_client = MagicMock()
        mock_client.query.side_effect = Exception("Network Error")
        mock_schema = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        
        with pytest.raises(QueryError, match="Failed to execute query"):
            repo.refresh(QueryKey.KPI_TOTALS)

    def test_get_raw_query_success(self):
        """Live repository returns query string from source."""
        mock_source = MagicMock()
        mock_source.get_raw_query.return_value = "SELECT * FROM Sales"
        mock_client = MagicMock()
        mock_schema = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        result = repo.get_raw_query(QueryKey.SALES_BY_DATE)

        assert result == "SELECT * FROM Sales"
        mock_source.get_raw_query.assert_called_once_with(QueryKey.SALES_BY_DATE)

    def test_get_raw_query_not_found_raises_query_not_found_error(self):
        """Live repository raises QueryNotFoundError if source doesn't have the key."""
        mock_source = MagicMock()
        mock_source.get_raw_query.side_effect = QueryNotFoundError("Query not found for key")
        mock_client = MagicMock()
        mock_schema = MagicMock()

        repo = LiveRepository(mock_source, mock_schema, mock_client)
        
        with pytest.raises(QueryNotFoundError, match="Query not found for key"):
            repo.get_raw_query(QueryKey.SALES_BY_DATE)
