"""Comprehensive branch testing for UI builders."""

import polars as pl
import pytest
import dash_mantine_components as dmc
from presentation.builders.components import (
    build_sales_key_performance_indicator_cards,
    build_leaderboard,
    build_top_products_table
)
from domain import KeyPerformanceIndicatorConfig

class TestBuilderEdgeCases:
    def test_kpi_cards_with_all_nulls(self, kpi_config):
        """Verify KPI cards handle a single row of all nulls gracefully."""
        null_data = pl.DataFrame({
            "Revenue": [None],
            "Profit": [None],
            "Orders": [None],
            "AvgOrderValue": [None]
        })
        cards = build_sales_key_performance_indicator_cards(null_data, kpi_config)
        assert len(cards) == 4
        # Should default to 0 formatted
        assert "$0" in str(cards[0].children)

    def test_leaderboard_with_missing_optional_columns(self):
        """Verify leaderboard handles missing target/trend columns."""
        minimal_data = pl.DataFrame({
            "SalesPerson": ["Alice"],
            "Revenue": [1000]
        })
        stack = build_leaderboard(minimal_data)
        assert isinstance(stack, dmc.Stack)
        # Should render just the name and revenue without erroring on missing target
        assert "Alice" in str(stack.children)

    def test_top_products_table_empty_df(self):
        """Verify top products table handles empty DataFrame."""
        grid = build_top_products_table(pl.DataFrame())
        assert grid.rowData == []
        assert grid.columnDefs == []

    def test_leaderboard_empty_data(self):
        """Verify leaderboard handles empty data."""
        stack = build_leaderboard(pl.DataFrame())
        assert "No data" in str(stack.children)

    def test_kpi_cards_missing_delta_logic(self):
        """Verify KPI cards don't crash when delta_column is configured but missing from data."""
        config_with_delta = [
            KeyPerformanceIndicatorConfig("Revenue", "Revenue", lambda v: str(v), delta_column="MissingDelta")
        ]
        data = pl.DataFrame({"Revenue": [100]})
        # Should not crash, just skip the badge
        cards = build_sales_key_performance_indicator_cards(data, config_with_delta)
        assert len(cards) == 1
        # No Badge in layout
        assert "Badge" not in str(cards[0].children)
