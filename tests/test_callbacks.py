"""Tests for dashboard callbacks."""

from unittest.mock import MagicMock
from unittest.mock import patch
import pytest
from domain import QueryNotFoundError, QueryKey
from presentation.callbacks.inspector import handle_inspector_logic


class TestCallbacks:
    def test_handle_inspector_success(self):
        """Inspector returns DAX query for selected chart."""
        mock_repo = MagicMock()
        mock_repo.get_raw_query.return_value = "EVALUATE 'Sales'"

        # Simulate Dash callback context
        with patch("presentation.callbacks.inspector.callback_context") as mock_ctx:
            # Use valid enum member values from QueryKey
            mock_ctx.triggered_id = {"type": "open-dax-inspector", "chart": QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS.value}

            result = handle_inspector_logic(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS.value, False, mock_repo)

            assert result.is_open is True
            assert result.content == "EVALUATE 'Sales'"

    def test_handle_inspector_query_not_found(self):
        """Inspector returns error message if query not found."""
        mock_repo = MagicMock()
        mock_repo.get_raw_query.side_effect = QueryNotFoundError("Missing")

        with patch("presentation.callbacks.inspector.callback_context") as mock_ctx:
            mock_ctx.triggered_id = {"type": "open-dax-inspector", "chart": QueryKey.TREND_DATA.value}

            result = handle_inspector_logic(QueryKey.TREND_DATA.value, False, mock_repo)
            assert "Query not found" in result.content

    def test_handle_inspector_repo_error(self):
        """Inspector returns error if repository fails."""
        mock_repo = MagicMock()
        mock_repo.get_raw_query.side_effect = RuntimeError("Not found")

        with patch("presentation.callbacks.inspector.callback_context") as mock_ctx:
            mock_ctx.triggered_id = {"type": "open-dax-inspector", "chart": QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS.value}

            result = handle_inspector_logic(QueryKey.KEY_PERFORMANCE_INDICATOR_TOTALS.value, False, mock_repo)
            assert "Repository error" in result.content

    def test_handle_inspector_empty_id(self):
        """Inspector shows prompt if no chart selected."""
        result = handle_inspector_logic("", False, MagicMock())
        assert "Select a chart" in result.content
