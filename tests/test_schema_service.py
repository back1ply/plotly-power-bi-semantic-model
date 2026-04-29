"""Tests for SchemaService."""

import pytest
from unittest.mock import MagicMock
from domain import QueryError, ModelSchema, QueryKey
from infrastructure.schema_service import SchemaService


class TestSchemaService:
    @pytest.fixture
    def mock_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_queries(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_client, mock_queries):
        return SchemaService(mock_client, mock_queries)

    def test_get_schema_success(self, service, mock_client, mock_queries):
        """get_schema parses raw records into ModelSchema dataclasses."""
        mock_queries.get_raw_query.return_value = "SCHEMA DAX"
        mock_client.query.return_value = [
            {"Table": "Sales", "Name": "Amount", "Type": "Column"},
            {"Table": "Sales", "Name": "TotalSales", "Type": "Measure"},
            {"Table": "Date", "Name": "Year", "Type": "Column"},
            {"Table": "Date", "Name": "RowNumber", "Type": "Column"}, # Should be filtered
        ]

        schema = service.get_schema()

        assert isinstance(schema, ModelSchema)
        assert "Sales" in schema.tables
        assert "Date" in schema.tables
        assert "Amount" in schema.tables["Sales"].columns
        assert "TotalSales" in schema.tables["Sales"].measures
        assert "Year" in schema.tables["Date"].columns
        assert "RowNumber" not in schema.tables["Date"].columns

    def test_get_schema_sorting(self, service, mock_client, mock_queries):
        """get_schema sorts tables and their internal lists."""
        mock_queries.get_raw_query.return_value = "SCHEMA DAX"
        mock_client.query.return_value = [
            {"Table": "B", "Name": "Z", "Type": "Column"},
            {"Table": "B", "Name": "A", "Type": "Column"},
            {"Table": "A", "Name": "X", "Type": "Column"},
        ]

        schema = service.get_schema()

        assert list(schema.tables.keys()) == ["A", "B"]
        assert schema.tables["B"].columns == ["A", "Z"]

    def test_get_schema_failure(self, service, mock_client, mock_queries):
        """get_schema raises QueryError on client failure."""
        mock_client.query.side_effect = Exception("PBI Error")
        with pytest.raises(QueryError, match="Failed to fetch model schema"):
            service.get_schema()

    def test_get_relationships_success(self, service, mock_client, mock_queries):
        """get_relationships returns raw list from client."""
        expected = [{"FromTable": "A", "ToTable": "B"}]
        mock_client.query.return_value = expected

        result = service.get_relationships()

        assert result[0].from_table == "A"
        assert result[0].to_table == "B"

    def test_get_relationships_failure(self, service, mock_client, mock_queries):
        """get_relationships raises QueryError on failure."""
        mock_client.query.side_effect = Exception("Net Error")
        with pytest.raises(QueryError, match="Failed to fetch model relationships"):
            service.get_relationships()
