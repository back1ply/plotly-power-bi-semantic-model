"""Tests for QueryService."""

import pytest
from unittest.mock import MagicMock
from domain import DataAnalysisExpressionsFragment, DataAnalysisExpressionsTemplate, QueryKey, QueryNotFoundError, FragmentCategory
from infrastructure.query_service import QueryService


class TestQueryService:
    @pytest.fixture
    def mock_loader(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_loader):
        return QueryService(mock_loader)

    def test_get_raw_query_success(self, service, mock_loader):
        """get_raw_query delegates to loader."""
        mock_loader.get_raw_query.return_value = "EVALUATE Table"
        result = service.get_raw_query(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS)
        assert result == "EVALUATE Table"
        mock_loader.get_raw_query.assert_called_once_with(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS)

    def test_get_raw_query_not_found(self, service, mock_loader):
        """get_raw_query raises QueryNotFoundError on loader error."""
        mock_loader.get_raw_query.side_effect = QueryNotFoundError("Missing")
        with pytest.raises(QueryNotFoundError, match="Query not found for key"):
            service.get_raw_query(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS)

    def test_get_query_template_success(self, service, mock_loader):
        """get_query_template delegates to loader."""
        mock_loader.get_query_template.return_value = DataAnalysisExpressionsTemplate("SELECT {col} FROM Table", "my_template")
        result = service.get_query_template("my_template")
        assert result.content == "SELECT {col} FROM Table"
        mock_loader.get_query_template.assert_called_once_with("my_template")

    def test_get_fragment_success(self, service, mock_loader):
        """get_fragment delegates to loader with Enum."""
        mock_loader.get_fragment.return_value = DataAnalysisExpressionsFragment("'Table'[Measure]", FragmentCategory.MEASURE, "Revenue")
        result = service.get_fragment(FragmentCategory.MEASURE, "Revenue")
        assert result.content == "'Table'[Measure]"
        mock_loader.get_fragment.assert_called_once_with(FragmentCategory.MEASURE, "Revenue")

    def test_get_formatted_query_success(self, service, mock_loader):
        """get_formatted_query formats template with parameters."""
        mock_loader.get_query_template.return_value = DataAnalysisExpressionsTemplate("EVALUATE FILTER(Table, [Col] = {val})", "template_key")
        result = service.get_formatted_query("template_key", parameters={"val": 100})
        assert result == "EVALUATE FILTER(Table, [Col] = 100)"

    def test_get_summarized_query_text_success(self, service, mock_loader):
        """get_summarized_query_text combines fragments and template."""
        mock_loader.get_fragment.side_effect = lambda cat, key: DataAnalysisExpressionsFragment(f"[{key}]", cat, key)
        mock_loader.get_query_template.return_value = DataAnalysisExpressionsTemplate("SUMMARIZECOLUMNS({columns} {measures})", "summarizecolumns")

        result = service.get_summarized_query_text("Revenue", "Category")

        assert "SUMMARIZECOLUMNS" in result
        assert "[Category]," in result
        assert '"Revenue", [Revenue]' in result

    def test_get_summarized_query_text_not_found(self, service, mock_loader):
        """get_summarized_query_text raises if fragment is missing."""
        mock_loader.get_fragment.side_effect = QueryNotFoundError("Missing")
        with pytest.raises(QueryNotFoundError, match="Template or fragments not found"):
            service.get_summarized_query_text("Revenue", "Category")

