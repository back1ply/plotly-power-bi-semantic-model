"""Tests for Home Page layout logic."""

from unittest.mock import MagicMock, patch
import polars as pl
import pytest
import dash_mantine_components as dmc
from domain import QueryError

# Patch dash.register_page before importing pages.home to avoid PageError
with patch("dash.register_page"):
    from pages.home import serve_layout


class TestHomeLayout:
    def test_serve_layout_success(self):
        """Layout is rendered correctly when repository returns data."""
        mock_repo = MagicMock()
        # Mocking all required data keys with expected columns and parsable dates
        # Column names must match what builders/components.py and figures.py expect (Revenue, not SalesAmount)
        mock_data = pl.DataFrame({
            "Revenue": [1000],
            "Profit": [500],
            "Orders": [10],
            "AvgOrderValue": [100],
            "Product": ["Test"],
            "Category": ["Test"],
            "Fiscal Year": [2024],
            "Month": ["2024-01-01"],
            "Group": ["Test"]
        })
        mock_repo.get_data.return_value = mock_data

        layout = serve_layout(mock_repo)
        
        # Verify structure
        assert isinstance(layout, dmc.Stack)
        assert len(layout.children) > 0
        assert any(isinstance(c, dmc.Title) for c in layout.children)

    def test_serve_layout_error(self):
        """Layout shows alert when repository fails."""
        mock_repo = MagicMock()
        mock_repo.get_data.side_effect = QueryError("Fetch failed")

        layout = serve_layout(mock_repo)
        
        assert isinstance(layout, dmc.Alert)
        assert "Fetch failed" in str(layout.children)
