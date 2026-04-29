"""Home Page - Executive Summary Dashboard.

Main dashboard page displaying:
- KPI cards (Revenue, Profit, Orders, AvgOrderValue)
- Sales trend chart by fiscal year
- Custom Insights dynamic chart builder (Category, Territory Group, Country, Month)
- Revenue by territory bar chart
- Top products table

This is the root page (/) of the application.
"""

import dash
import dash_mantine_components as dmc
import plotly.graph_objects as go
from dash import dcc
from dash import html

from components.base import build_dax_inspector_button
from domain import DataPort
from domain import KpiConfig
from domain import QueryError
from domain import QueryKey
from presentation.charts import build_sales_kpi_cards
from presentation.charts import build_sales_trend_chart
from presentation.charts import build_territory_sales_chart
from presentation.charts import build_top_products_table
from presentation.constants import DIMENSION_LABELS
from presentation.constants import MEASURE_LABELS
from presentation.dependency import get_repository
from presentation.formatters import format_currency_two_decimals
from presentation.formatters import format_currency_zero_decimal
from presentation.formatters import format_integer
from presentation.helpers import create_empty_figure

# Register page at module level (Standard Dash Pages pattern)
dash.register_page(
    __name__,
    path="/",
    name="Executive Summary",
    order=1,
)

# Query key constant for the dynamic chart
CUSTOM_INSIGHTS = "custom_insights"

# KPI configuration with formatters (OO-001)
KPI_CONFIG = [
    KpiConfig(
        "Revenue",
        "Revenue",
        format_currency_zero_decimal,
        icon="tabler:currency-dollar",
        color="blue",
    ),
    KpiConfig(
        "Profit",
        "Profit",
        format_currency_zero_decimal,
        icon="tabler:trending-up",
        color="teal",
    ),
    KpiConfig("Orders", "Orders", format_integer, icon="tabler:shopping-cart", color="orange"),
    KpiConfig(
        "Avg Order Value",
        "AvgOrderValue",
        format_currency_two_decimals,
        icon="tabler:receipt",
        color="violet",
    ),
]

# Graph config - hide Plotly modebar
_GRAPH_CONFIG = {"displayModeBar": False}


# Validation layout fragment for app.py (OO-002)
VALIDATION_LAYOUT = html.Div(
    [
        dcc.Graph(id="home-builder-graph"),
        dmc.Select(id="home-builder-measure"),
        dmc.Select(id="home-builder-dimension"),
        dmc.LoadingOverlay(id="home-builder-loading"),
    ]
)


def _build_card(
    title: str, query_key: QueryKey, content: dash.development.base_component.Component
) -> dmc.Paper:
    """Create card with title, DAX inspector button, and content."""
    return dmc.Paper(
        p="md",
        withBorder=True,
        radius="md",
        shadow="sm",
        children=[
            dmc.Group(
                justify="space-between",
                mb="md",
                children=[
                    dmc.Text(title, fw=600),
                    build_dax_inspector_button(query_key),
                ],
            ),
            content,
        ],
    )


def _build_graph(figure: go.Figure, chart_id: str = "") -> dcc.Graph:
    """Create Graph component with shared config."""
    props = {"config": _GRAPH_CONFIG, "figure": figure}
    if chart_id:
        props["id"] = chart_id
    return dcc.Graph(**props)


def layout() -> dmc.Stack | dmc.Alert:
    """Create executive summary dashboard layout."""
    repo = get_repository(DataPort)
    return serve_layout(repo)


def serve_layout(repo: DataPort) -> dmc.Stack | dmc.Alert:
    """Logic to build the layout, separated for testability. (OO-002)"""
    # Fetch data from repository
    try:
        kpi_data = repo.get_data(QueryKey.KPI_TOTALS)
        trend_data = repo.get_data(QueryKey.SALES_BY_DATE)
        territory_data = repo.get_data(QueryKey.SALES_BY_TERRITORY)
        product_data = repo.get_data(QueryKey.TOP_N_PRODUCTS)
    except QueryError as exc:
        return dmc.Alert(
            f"Failed to load dashboard data: {exc}",
            title="Data Fetch Error",
            color="red",
            variant="filled",
            icon="tabler:alert-circle",
            mt="xl",
        )

    return dmc.Stack(
        gap="xl",
        children=[
            dmc.Title("Executive Summary", order=3, fw=700, mt="md"),
            dmc.SimpleGrid(
                cols=4,
                spacing="md",
                children=build_sales_kpi_cards(kpi_data, KPI_CONFIG),
            ),
            _build_card(
                "Sales Trend",
                QueryKey.SALES_BY_DATE,
                _build_graph(build_sales_trend_chart(trend_data), "trend-chart"),
            ),
            dmc.Grid(
                gutter="md",
                children=[
                    dmc.GridCol(
                        span=6,
                        children=dmc.Paper(
                            p="md",
                            withBorder=True,
                            radius="md",
                            shadow="sm",
                            children=[
                                dmc.Group(
                                    justify="space-between",
                                    mb="md",
                                    children=[
                                        dmc.Text("Custom Insights", fw=600),
                                        build_dax_inspector_button(CUSTOM_INSIGHTS),
                                    ],
                                ),
                                dmc.SimpleGrid(
                                    cols=2,
                                    mb="md",
                                    children=[
                                        dmc.Select(
                                            id="home-builder-measure",
                                            label="Measure",
                                            data=[{"label": k, "value": k} for k in MEASURE_LABELS],
                                            value="Revenue",
                                            size="xs",
                                        ),
                                        dmc.Select(
                                            id="home-builder-dimension",
                                            label="Dimension",
                                            data=[
                                                {"label": k, "value": k} for k in DIMENSION_LABELS
                                            ],
                                            value="Category",
                                            size="xs",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    style={"position": "relative"},
                                    children=[
                                        dmc.LoadingOverlay(
                                            visible=False, id="home-builder-loading"
                                        ),
                                        _build_graph(
                                            create_empty_figure("Loading..."),
                                            "home-builder-graph",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                    dmc.GridCol(
                        span=6,
                        children=_build_card(
                            "Revenue by Territory",
                            QueryKey.SALES_BY_TERRITORY,
                            _build_graph(build_territory_sales_chart(territory_data)),
                        ),
                    ),
                ],
            ),
            _build_card(
                "Product Performance",
                QueryKey.TOP_N_PRODUCTS,
                build_top_products_table(product_data),
            ),
        ],
    )
