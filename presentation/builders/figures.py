from typing import Any

import plotly.graph_objects as go

from domain.ports import DataFrame
from presentation.helpers import create_empty_figure
from presentation.helpers import hex_to_rgba
from presentation.theme import CATEGORICAL_PALETTE
from presentation.theme import CHART_PALETTE
from presentation.theme import COLORS
from presentation.theme import DESIGN_TOKENS
from presentation.builders.constants import Orientation, SortOrder

_LAYOUT_DEFAULTS = {"height": 300, "margin": {"l": 50, "r": 20, "t": 20, "b": 40}}
_TREND_PALETTE = CHART_PALETTE


def _create_layout(height: int | None = None) -> dict[str, Any]:
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
            "tickformat": "$.2s",
        },
        "hoverlabel": {
            "bgcolor": COLORS["plot"],
            "font": {"family": "Inter, sans-serif", "size": 13},
        },
        "height": height or _LAYOUT_DEFAULTS["height"],
    }


def _ensure_dataframe(data: Any) -> DataFrame:
    """Ensure data is a DataFrame protocol implementation."""
    return data


def _validate_chart_data(data_frame: DataFrame, required_columns: set[str]) -> bool:
    return not data_frame.is_empty() and required_columns.issubset(set(data_frame.columns))


def build_sparkline_figure(values: list[float], color: str) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            y=values,
            mode="lines",
            line={"width": 1.5, "color": color, "shape": "spline"},
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, 0.1),
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        height=40,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        showlegend=False,
    )
    return fig


def build_bar_chart(
    data: DataFrame,
    x_column: str,
    y_column: str,
    *,
    color: str | list[str] = COLORS["primary"],
    orientation: Orientation = Orientation.VERTICAL,
    sort_order: SortOrder = SortOrder.NONE,
) -> go.Figure:
    data_frame = _ensure_dataframe(data)
    if not _validate_chart_data(data_frame, {x_column, y_column}):
        return create_empty_figure()

    if sort_order != SortOrder.NONE:
        if orientation == Orientation.HORIZONTAL:
            descending = sort_order == SortOrder.ASCENDING
        else:
            descending = sort_order == SortOrder.DESCENDING

        data_frame = data_frame.sort(y_column, descending=descending)

    if orientation == Orientation.HORIZONTAL:
        x_axis_data, y_axis_data = data_frame.get_column(y_column), data_frame.get_column(x_column)
        text_template = "%{x:$.2s}"
        hover_template = f"<b>%{{y}}</b><br>{y_column}: %{{x:$,.0f}}<extra></extra>"
    else:
        x_axis_data, y_axis_data = data_frame.get_column(x_column), data_frame.get_column(y_column)
        text_template = "%{y:$.2s}"
        hover_template = f"<b>%{{x}}</b><br>{y_column}: %{{y:$,.0f}}<extra></extra>"

    figure = go.Figure(
        data=[
            go.Bar(
                x=x_axis_data,
                y=y_axis_data,
                marker_color=color,
                orientation=orientation,
                text=y_axis_data if orientation == "v" else x_axis_data,
                texttemplate=text_template,
                textposition="outside",
                cliponaxis=False,
                hovertemplate=hover_template,
            )
        ]
    )

    layout_config = _create_layout()
    if orientation == "h":
        layout_config["xaxis"].update(
            {"showgrid": True, "gridcolor": COLORS["grid"], "tickformat": "$.2s"}
        )
        layout_config["yaxis"].update({"showgrid": False, "tickformat": None})

    figure.update_layout(**layout_config)
    return figure


def build_sales_trend_chart(
    data: DataFrame,
    x_column: str = "Month",
    y_column: str = "Revenue",
    group_column: str = "Fiscal Year",
    sort_column: str = "Month",
) -> go.Figure:
    data_frame = _ensure_dataframe(data)
    if not _validate_chart_data(data_frame, {group_column, sort_column, x_column, y_column}):
        return create_empty_figure()

    data_frame = data_frame.cast_date(sort_column, "_sort_key")
    data_frame = data_frame.format_date("_sort_key", x_column, "%b")
    data_frame_sorted = data_frame.sort("_sort_key")
    month_order = data_frame_sorted.get_column(x_column).unique(maintain_order=True).to_list()

    figure = go.Figure()
    unique_groups = (
        data_frame_sorted.get_column(group_column).unique().sort(descending=True).to_list()
    )

    for group_index, group_val in enumerate(unique_groups):
        color = _TREND_PALETTE[group_index % len(_TREND_PALETTE)]
        group_data_frame = data_frame_sorted.filter(**{group_column: group_val})

        figure.add_trace(
            go.Scatter(
                x=group_data_frame.get_column(x_column),
                y=group_data_frame.get_column(y_column),
                mode="lines+markers",
                name=str(group_val),
                line={"width": 3, "color": color, "shape": "spline"},
                marker={"size": 6},
                fill="tozeroy",
                fillcolor=hex_to_rgba(color, 0.05),
                hovertemplate="%{y:$,.0f}<extra></extra>",
            )
        )

    layout_config = _create_layout()
    layout_config["xaxis"].update(
        {
            "type": "category",
            "categoryorder": "array",
            "categoryarray": month_order,
            "showspikes": True,
            "spikecolor": "rgba(255,255,255,0.16)",
            "spikethickness": 1,
            "spikedash": "dot",
            "spikemode": "across+toaxis",
        }
    )

    figure.update_layout(
        **layout_config,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.1, "x": 1, "xanchor": "right"},
    )
    return figure


def build_category_sales_chart(
    data: DataFrame,
    category_column: str = "Category",
    value_column: str = "Revenue",
) -> go.Figure:
    return build_bar_chart(
        data,
        category_column,
        value_column,
        color=CATEGORICAL_PALETTE,
        orientation=Orientation.HORIZONTAL,
        sort_order=SortOrder.DESCENDING,
    )


def build_territory_sales_chart(
    data: DataFrame,
    group_column: str = "Group",
    value_column: str = "Revenue",
) -> go.Figure:
    data_frame = _ensure_dataframe(data)
    if not _validate_chart_data(data_frame, {group_column, value_column}):
        return create_empty_figure()

    data_frame_aggregated = data_frame.aggregate(by=group_column, aggregations={value_column: "sum"})

    return build_bar_chart(
        data_frame_aggregated,
        group_column,
        value_column,
        color=CATEGORICAL_PALETTE,
        orientation=Orientation.HORIZONTAL,
        sort_order=SortOrder.DESCENDING,
    )


def build_category_bars_chart(
    data: DataFrame,
    category_column: str = "Category",
    value_column: str = "Revenue",
) -> go.Figure:
    data_frame = _ensure_dataframe(data)
    if not _validate_chart_data(data_frame, {category_column, value_column}):
        return create_empty_figure()

    data_frame = data_frame.sort(value_column, descending=False)
    accent = DESIGN_TOKENS["accent"]
    n = len(data_frame)
    bar_colors = [hex_to_rgba(accent, 0.4 + 0.6 * i / max(n - 1, 1)) for i in range(n)]

    figure = go.Figure(
        go.Bar(
            x=data_frame.get_column(value_column),
            y=data_frame.get_column(category_column),
            orientation="h",
            marker={"color": bar_colors, "line": {"width": 0}},
            text=data_frame.get_column(value_column),
            texttemplate="%{x:$.2s}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:$,.0f}<extra></extra>",
        )
    )

    layout_config = _create_layout()
    layout_config["xaxis"].update(
        {"showgrid": True, "gridcolor": COLORS["grid"], "tickformat": "$.2s"}
    )
    layout_config["yaxis"].update({"showgrid": False, "tickformat": None})
    figure.update_layout(**layout_config)
    return figure


def build_profitability_matrix(
    data: DataFrame,
    row_column: str = "Region",
    col_column: str = "Category",
    value_column: str = "MarginPct",
) -> go.Figure:
    data_frame = _ensure_dataframe(data)
    if not _validate_chart_data(data_frame, {row_column, col_column, value_column}):
        return create_empty_figure()

    pivoted = data_frame.pivot(
        index=row_column,
        on=col_column,
        values=value_column,
        aggregate_function="mean",
    )
    row_labels = pivoted.get_column(row_column).to_list()
    col_labels = [c for c in pivoted.columns if c != row_column]
    # In library-agnostic mode, we might need a way to get numpy array or similar.
    # But for now, let's assume we can work with nested lists or similar.
    # If the protocol doesn't support to_numpy(), we might need to add it or use select + iterate.
    z_values = pivoted.select(col_labels).to_dicts() # This returns list[dict]
    # Convert list[dict] to nested list for heatmap
    z_matrix = [[row[col] for col in col_labels] for row in z_values]
    
    text_values = [[f"{v:.1f}%" if v is not None else "" for v in row] for row in z_matrix]

    figure = go.Figure(
        go.Heatmap(
            z=z_matrix,
            x=col_labels,
            y=row_labels,
            colorscale=[

                [0.0, DESIGN_TOKENS["neg"]],
                [0.5, "#1e1e2e"],
                [1.0, DESIGN_TOKENS["accent"]],
            ],
            zmid=0,
            showscale=False,
            xgap=2,
            ygap=2,
            text=text_values,
            texttemplate="%{text}",
            hovertemplate="<b>%{y} × %{x}</b><br>Margin: %{z:.1f}%<extra></extra>",
        )
    )

    layout_config = _create_layout()
    layout_config["margin"] = {"l": 80, "r": 20, "t": 20, "b": 60}
    layout_config["xaxis"].update({"showgrid": False})
    layout_config["yaxis"].update({"showgrid": False, "tickformat": None, "autorange": "reversed"})
    figure.update_layout(**layout_config)
    return figure
