"""Tests for Chart and Visualization Builders."""

import polars as pl
import plotly.graph_objects as go
import dash_mantine_components as dmc
import dash_ag_grid as dag
import pytest
from domain import DataFrame
from presentation.builders.components import (
    build_sales_key_performance_indicator_cards,
    build_top_products_table
)
from presentation.builders.figures import (
    build_sales_trend_chart,
    build_category_sales_chart,
    build_territory_sales_chart,
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
    def _get_kpi_value_text(self, card: dmc.Paper) -> str:
        """Navigate card structure: Paper.children[1] = Group(value_Text, *delta)."""
        paper_children = card.children
        assert isinstance(paper_children, list)
        value_group = paper_children[1]
        assert isinstance(value_group, dmc.Group)
        group_children = value_group.children
        assert isinstance(group_children, list)
        value_text = group_children[0]
        assert isinstance(value_text, dmc.Text)
        return str(value_text.children)

    def test_empty_data_returns_zeroed_cards(self, kpi_config):
        """build_sales_key_performance_indicator_cards handles empty DataFrame by zeroing out values."""
        cards = build_sales_key_performance_indicator_cards(pl.DataFrame(), kpi_config)
        assert len(cards) == 4
        assert "$0" in self._get_kpi_value_text(cards[0])

    def test_kpi_formatting_logic(self, sample_kpi_df, kpi_config):
        """Verify currency and integer formatting in KPI cards."""
        cards = build_sales_key_performance_indicator_cards(sample_kpi_df, kpi_config)
        assert "$1,250,000" in self._get_kpi_value_text(cards[0])
        orders_value = self._get_kpi_value_text(cards[2])
        assert "1,450" in orders_value
        assert "$" not in orders_value


class TestMakeTrendChart:
    def test_empty_data_returns_empty_figure(self):
        fig = build_sales_trend_chart(pl.DataFrame())
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
        # ISO strings "2022-07-01" -> "Jul", "2023-01-01" -> "Jan"
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
        fig = build_category_sales_chart(pl.DataFrame())
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
        
        # Revenue now uses inline bar cellRenderer instead of valueFormatter
        sales_col = next(c for c in grid.columnDefs if c["field"] == "Revenue")
        assert "cellRenderer" in sales_col
        assert "max" in sales_col["cellRendererParams"]
        assert sales_col["cellRendererParams"]["max"] > 0
