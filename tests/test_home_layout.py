"""Tests for Home Page Layout."""

import dash_mantine_components as dmc
from unittest.mock import MagicMock, patch
import pytest

# Mock register_page before importing pages.home
with patch("dash.register_page"):
    from pages.home import serve_layout

from domain import QueryError


class TestHomeLayout:
    def test_serve_layout_success(self):
        """Layout is rendered correctly when repository returns data."""
        mock_repo = MagicMock()
        # Mocking all required data keys
        mock_repo.get_data.return_value = [{"col": 1}]

        layout = serve_layout(mock_repo)

        assert isinstance(layout, dmc.Stack)
        # Verify repo was called for each key
        assert mock_repo.get_data.call_count == 4

    def test_serve_layout_fetch_error_displays_alert(self):
        """Alert is displayed if repository raises QueryError."""
        mock_repo = MagicMock()
        mock_repo.get_data.side_effect = QueryError("PBI Error")

        layout = serve_layout(mock_repo)

        assert isinstance(layout, dmc.Alert)
        assert "PBI Error" in layout.children
