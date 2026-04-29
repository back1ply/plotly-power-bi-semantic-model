"""Chart and Visualization Builders.

Pure functions for creating Plotly charts and Dash components from DataFrames.
These functions are decoupled from data infrastructure and caching.
"""

from enum import StrEnum
from typing import Any

import dash_ag_grid as dag
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash_iconify import DashIconify

from domain import KpiConfig
from presentation.helpers import create_empty_figure
from presentation.theme import CATEGORICAL_PALETTE
from presentation.theme import COLORS


class Orientation(StrEnum):
    VERTICAL = "v"
    HORIZONTAL = "h"


class SortOrder(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"
    NONE = "none"


_LAYOUT_DEFAULTS = {"height": 300, "margin": {"l": 50, "r": 20, "t": 20, "b": 40}}


def _hex_to_rgba(hex_color: str, opacity: float) -> str:
    """Convert hex color to rgba string with given opacity."""
    hex_color = hex_color.lstrip("#")
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


# Premium palette for trend lines (Mantine colors)
_TREND_PALETTE = ["#4c6ef5", "#fa5252", "#12b886", "#be4bdb", "#fd7e14"]


def _create_layout(height: int | None = None) -> dict[str, Any]:
    """Create consistent Plotly layout config."""
    return {
        "template": "plotly_dark",
        "margin": {"l": 80, "r": 60, "t": 20, "b": 40},
        "paper_bgcolor": COLORS["bg"],
        "plot_bgcolor": COLORS["plot"],
        "font": {"family": "Inter, sans-serif", "color": COLORS["text"]},
        "xaxis": {
            "showgrid": False,
            "zeroline": False,
            "tickfont": {"size": 11},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": COLORS["grid"],
            "zeroline": False,
            "tickfont": {"size": 11},
            "tickformat": "$.2s",  # Compact currency: $1.2M
        },
        "hoverlabel": {
            "bgcolor": COLORS["plot"],
            "font": {"family": "Inter, sans-serif", "size": 13},
        },
        "height": height or _LAYOUT_DEFAULTS["height"],
    }


def _ensure_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Validate that input is a DataFrame."""
    if not isinstance(data, pd.DataFrame):
        return pd.DataFrame(data)
    return data


def _validate_chart_data(df: pd.DataFrame, required_columns: set[str]) -> bool:
    """Check if dataframe is not empty and contains required columns."""
    return not df.empty and required_columns.issubset(df.columns)


def build_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    *,
    color: str | list[str] = COLORS["primary"],
    orientation: Orientation = Orientation.VERTICAL,
    sort_order: SortOrder = SortOrder.NONE,
) -> go.Figure:
    """Create a bar chart from data columns with optional sorting and orientation."""
    df = _ensure_dataframe(data)
    if not _validate_chart_data(df, {x_column, y_column}):
        return create_empty_figure()

    # Apply sorting if requested
    if sort_order != SortOrder.NONE:
        # If horizontal, we reverse the logic because Plotly plots from bottom to top.
        if orientation == Orientation.HORIZONTAL:
            ascending = sort_order == SortOrder.DESCENDING
        else:
            ascending = sort_order == SortOrder.ASCENDING

        df = df.sort_values(by=y_column, ascending=ascending)

    # Configure axes based on orientation
    if orientation == Orientation.HORIZONTAL:
        x_data, y_data = df[y_column], df[x_column]
        text_template = "%{x:$.2s}"
        hover_template = f"<b>%{{y}}</b><br>{y_column}: %{{x:$,.0f}}<extra></extra>"
    else:
        x_data, y_data = df[x_column], df[y_column]
        text_template = "%{y:$.2s}"
        hover_template = f"<b>%{{x}}</b><br>{y_column}: %{{y:$,.0f}}<extra></extra>"

    fig = go.Figure(
        data=[
            go.Bar(
                x=x_data,
                y=y_data,
                marker_color=color,
                orientation=orientation,
                text=y_data if orientation == "v" else x_data,
                texttemplate=text_template,
                textposition="outside",
                cliponaxis=False,
                hovertemplate=hover_template,
            )
        ]
    )

    layout_config = _create_layout()
    if orientation == "h":
        # Swap tick formats and grid visibility for horizontal chart
        layout_config["xaxis"].update(
            {"showgrid": True, "gridcolor": COLORS["grid"], "tickformat": "$.2s"}
        )
        layout_config["yaxis"].update({"showgrid": False, "tickformat": None})

    fig.update_layout(**layout_config)
    return fig


def build_sales_kpi_cards(
    data: pd.DataFrame,
    kpi_config: list[KpiConfig],
) -> list[dmc.Paper]:
    """Create PBI-style KPI cards: colored left border, ThemeIcon, uppercase label, large value."""
    df = _ensure_dataframe(data)
    row = df.iloc[0] if not df.empty else None

    cards = []
    for c in kpi_config:
        value = c.formatter(row.get(c.column, 0) or 0) if row is not None else c.formatter(0)

        cards.append(
            dmc.Paper(
                p="md",
                withBorder=True,
                radius="md",
                style={"borderLeft": f"3px solid var(--mantine-color-{c.color}-6)"},
                children=[
                    dmc.Group(
                        justify="space-between",
                        mb="sm",
                        children=[
                            dmc.Text(
                                c.label,
                                c="dimmed",
                                size="xs",
                                tt="uppercase",
                                fw=700,
                                lts=0.5,
                            ),
                            dmc.ThemeIcon(
                                DashIconify(icon=c.icon, width=18),
                                size=34,
                                radius="md",
                                color=c.color,
                                variant="light",
                            )
                            if c.icon
                            else None,
                        ],
                    ),
                    dmc.Text(value, size="xl", fw=700),
                ],
            )
        )

    return cards


def build_sales_trend_chart(
    data: pd.DataFrame,
    x_column: str = "Month",
    y_column: str = "SalesAmount",
    group_column: str = "Fiscal Year",
    sort_column: str = "Month",
) -> go.Figure:
    """Create multi-line trend chart for sales over time with year-over-year overlap."""
    df = _ensure_dataframe(data)
    if not _validate_chart_data(df, {group_column, sort_column, x_column, y_column}):
        return create_empty_figure()

    # Pre-process: ensure overlapping X-axis by extracting month name
    df = df.copy()

    # Store original sort values before transforming x_column
    # Use pandas to handle the date strings reliably
    df["_sort_key"] = pd.to_datetime(df[sort_column])

    # Robustly extract the month name from the string (e.g. "2019-07-01..." -> "Jul")
    # Using datetime dt.strftime is safer than regex on the raw string
    df[x_column] = df["_sort_key"].dt.strftime("%b")

    # Sort to extract the correct chronological month order
    df_sorted = df.sort_values(by=["_sort_key"])

    # Crucial: month_order must be based on the stripped names to align coordinates
    month_order = []
    for m in df_sorted[x_column].unique():
        if m not in month_order:
            month_order.append(m)

    fig = go.Figure()
    # Create a trace for each year, they will share the same X coordinates (Month names)
    # We sort groups descending to put the latest year at the front of the legend
    unique_groups = sorted(df_sorted[group_column].unique(), reverse=True)
    for i, group_val in enumerate(unique_groups):
        color = _TREND_PALETTE[i % len(_TREND_PALETTE)]
        group_df = df_sorted[df_sorted[group_column] == group_val]

        fig.add_trace(
            go.Scatter(
                x=group_df[x_column],
                y=group_df[y_column],
                mode="lines+markers",
                name=str(group_val),
                line={"width": 3, "color": color, "shape": "spline"},
                marker={"size": 6},
                fill="tozeroy",
                fillcolor=_hex_to_rgba(color, 0.05),
                hovertemplate="%{y:$,.0f}<extra></extra>",
            )
        )

    layout_config = _create_layout()
    layout_config["xaxis"].update(
        {
            "type": "category",
            "categoryorder": "array",
            "categoryarray": month_order,
        }
    )

    fig.update_layout(
        **layout_config,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.1, "x": 1, "xanchor": "right"},
    )
    return fig


def build_category_sales_chart(
    data: pd.DataFrame,
    category_column: str = "Category",
    value_column: str = "SalesAmount",
) -> go.Figure:
    """Create bar chart of sales by product category."""
    df = _ensure_dataframe(data)
    if not _validate_chart_data(df, {category_column, value_column}):
        return create_empty_figure()

    return build_bar_chart(
        df,
        category_column,
        value_column,
        color=CATEGORICAL_PALETTE,
        orientation=Orientation.HORIZONTAL,
        sort_order=SortOrder.DESCENDING,
    )


def build_territory_sales_chart(
    data: pd.DataFrame,
    group_column: str = "Group",
    value_column: str = "SalesAmount",
) -> go.Figure:
    """Create bar chart of sales by geographic territory."""
    df = _ensure_dataframe(data)
    if not _validate_chart_data(df, {group_column, value_column}):
        return create_empty_figure()

    # Aggregate by group to avoid overlapping labels from country breakdown
    df_agg = df.groupby(group_column, as_index=False)[value_column].sum()

    if not isinstance(df_agg, pd.DataFrame):
        df_agg = pd.DataFrame(df_agg).reset_index()

    return build_bar_chart(
        df_agg,
        group_column,
        value_column,
        color=CATEGORICAL_PALETTE,
        orientation=Orientation.HORIZONTAL,
        sort_order=SortOrder.DESCENDING,
    )


def build_top_products_table(data: pd.DataFrame) -> dag.AgGrid:
    """Create AG Grid table of top products."""
    df = _ensure_dataframe(data)
    if df.empty:
        return dag.AgGrid(columnDefs=[], rowData=[])

    return dag.AgGrid(
        id="product-table",
        columnDefs=[
            {"field": "Product", "filter": True, "sortable": True, "flex": 2},
            {"field": "Category", "filter": True, "sortable": True, "flex": 1},
            {
                "field": "SalesAmount",
                "filter": "agNumberColumnFilter",
                "sortable": True,
                "flex": 1,
                "valueFormatter": {"function": "d3.format('$,.0f')(params.value)"},
            },
            {
                "field": "Profit",
                "filter": "agNumberColumnFilter",
                "sortable": True,
                "flex": 1,
                "valueFormatter": {"function": "d3.format('$,.0f')(params.value)"},
            },
        ],
        rowData=df.to_dict("records"),
        dashGridOptions={"theme": "themeQuartz"},
        style={"height": "400px", "width": "100%"},
    )
