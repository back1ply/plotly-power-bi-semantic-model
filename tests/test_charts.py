"""Tests for Chart and Visualization Builders."""

import pandas as pd
import plotly.graph_objects as go
import dash_mantine_components as dmc
import dash_ag_grid as dag
import pytest
from presentation.charts import (
    build_sales_kpi_cards,
    build_sales_trend_chart,
    build_category_sales_chart,
    build_territory_sales_chart,
    build_top_products_table
)
from presentation.helpers import create_empty_figure


class TestEmptyFigure:
    def test_empty_figure_properties(self):
        """create_empty_figure returns a styled, axis-free figure with message."""
        msg = "Custom Test Message"
        fig = create_empty_figure(msg, height=450)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.height == 450
        assert fig.layout.xaxis.visible is False
        assert fig.layout.yaxis.visible is False
        assert fig.layout.annotations[0].text == msg


class TestMakeKpiCards:
    def test_empty_data_returns_zeroed_cards(self, kpi_config):
        """build_sales_kpi_cards handles empty DataFrame by zeroing out values."""
        cards = build_sales_kpi_cards(pd.DataFrame(), kpi_config)
        assert len(cards) == 4
        # Verify first card (Revenue) shows $0
        revenue_title = cards[0].children[1]
        assert "$0" in revenue_title.children

    def test_kpi_formatting_logic(self, sample_kpi_df, kpi_config):
        """Verify currency and integer formatting in KPI cards."""
        cards = build_sales_kpi_cards(sample_kpi_df, kpi_config)
        
        # Revenue: $1,250,000
        assert "$1,250,000" in cards[0].children[1].children
        # Orders: 1,450 (integer, no $)
        assert "1,450" in cards[2].children[1].children
        assert "$" not in cards[2].children[1].children


class TestMakeTrendChart:
    def test_empty_data_returns_empty_figure(self):
        fig = build_sales_trend_chart(pd.DataFrame())
        assert len(fig.data) == 0

    def test_trend_chart_structure(self, sample_sales_df):
        """Verify year-over-year traces and categorical axis sorting (Fiscal Year starts in July)."""
        fig = build_sales_trend_chart(sample_sales_df)
        
        # 2 unique years in sample = 2 traces
        assert len(fig.data) == 2
        names = {t.name for t in fig.data}
        assert names == {"2023", "2024"}
        
        # Verify categorical axis order (Fiscal year starting July in sample)
        assert fig.layout.xaxis.type == "category"
        # July is Fiscal Month 1, January is 7. So July MUST come first in overlapping sort.
        assert list(fig.layout.xaxis.categoryarray) == ["Jul", "Jan"]


class TestMakeCategoryChart:
    def test_category_chart_sorting(self, sample_category_df):
        """build_category_sales_chart applies sorting to put largest categories at top."""
        fig = build_category_sales_chart(sample_category_df)
        
        assert fig.data[0].orientation == "h"
        # Largest value (Bikes: 800k) should be at the end of the Y list for bottom-up Plotly plotting
        assert list(fig.data[0].y) == ["Clothing", "Accessories", "Bikes"]
        assert list(fig.data[0].x) == [200000, 250000, 800000]

    def test_category_chart_empty(self):
        fig = build_category_sales_chart(pd.DataFrame())
        assert len(fig.data) == 0


class TestMakeTerritoryChart:
    def test_territory_chart_aggregation(self, sample_territory_df):
        """build_territory_sales_chart aggregates by Group."""
        fig = build_territory_sales_chart(sample_territory_df)
        assert len(fig.data) == 1
        assert "Pacific" in list(fig.data[0].y)


class TestMakeProductTable:
    def test_product_table_definitions(self, sample_products_df):
        """Verify AG Grid configuration for product table."""
        grid = build_top_products_table(sample_products_df)
        
        assert isinstance(grid, dag.AgGrid)
        assert len(grid.rowData) == 3
        
        # Check for currency formatters
        sales_col = next(c for c in grid.columnDefs if c["field"] == "SalesAmount")
        assert "d3.format('$,.0f')" in sales_col["valueFormatter"]["function"]
