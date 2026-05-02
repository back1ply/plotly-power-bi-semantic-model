from typing import Any, cast

import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

from domain import KeyPerformanceIndicatorConfig
from domain.ports import DataFrame
from presentation.helpers import avatar_color
from presentation.helpers import initials
from presentation.theme import COLORS
from presentation.theme import DESIGN_TOKENS
from presentation.theme import MANTINE_SHADE5_TO_HEX
from presentation.builders.figures import build_sparkline_figure
from presentation.builders.figures import build_category_bars_chart


def _ensure_dataframe(data: Any) -> DataFrame:
    """Ensure the data satisfies the DataFrame protocol. (API-007)"""
    if isinstance(data, DataFrame):
        return data
    return cast(DataFrame, data)


def _validate_chart_data(data_frame: DataFrame, required_columns: set[str]) -> bool:
    """Check if the data frame has rows and required columns. (API-003)"""
    return not data_frame.is_empty() and required_columns.issubset(set(data_frame.columns))


def build_sales_key_performance_indicator_cards(
    data: DataFrame,
    key_performance_indicator_config: list[KeyPerformanceIndicatorConfig],
    sparkline_data: DataFrame | None = None,
) -> list[dmc.Paper]:
    data_frame = _ensure_dataframe(data)
    row = next(iter(data_frame.iter_rows(named=True)), None) if not data_frame.is_empty() else None

    cards = []
    for config in key_performance_indicator_config:
        raw_value = row.get(config.column, 0) if row is not None else 0
        value = config.formatter(raw_value or 0)
        accent_hex = MANTINE_SHADE5_TO_HEX.get(config.color, DESIGN_TOKENS["accent"])

        delta_children: list[Any] = []
        if config.delta_column and row is not None:
            delta_val = row.get(config.delta_column)
            if delta_val is not None:
                delta_float = float(delta_val)
                is_pos = delta_float >= 0
                arrow = "↑" if is_pos else "↓"
                badge_color = DESIGN_TOKENS["pos"] if is_pos else DESIGN_TOKENS["neg"]
                badge_bg = DESIGN_TOKENS["pos_bg"] if is_pos else DESIGN_TOKENS["neg_bg"]
                delta_children = [
                    dmc.Badge(
                        f"{arrow} {abs(delta_float):.1f}%",
                        variant="light",
                        size="sm",
                        style={"color": badge_color, "background": badge_bg, "fontWeight": 600},
                    )
                ]

        sparkline_children: list[Any] = []
        if sparkline_data is not None and config.column in sparkline_data.columns:
            sparkline_df = _ensure_dataframe(sparkline_data)
            vals = [r.get(config.column) for r in sparkline_df.iter_rows(named=True)]
            sparkline_children = [
                dcc.Graph(
                    figure=build_sparkline_figure(vals, accent_hex),
                    config={"displayModeBar": False},
                    style={"height": "40px", "marginTop": "8px"},
                )
            ]

        cards.append(
            dmc.Paper(
                p="md",
                withBorder=True,
                radius="md",
                style={"borderLeft": f"3px solid var(--mantine-color-{config.color}-6)"},
                children=[
                    dmc.Group(
                        justify="space-between",
                        mb="sm",
                        children=[
                            dmc.Text(
                                config.label,
                                c="dimmed",
                                size="xs",
                                tt="uppercase",
                                fw=700,
                                lts=0.5,
                            ),
                            dmc.ThemeIcon(
                                DashIconify(icon=config.icon, width=18),
                                size=34,
                                radius="md",
                                color=config.color,
                                variant="light",
                            )
                            if config.icon
                            else None,
                        ],
                    ),
                    dmc.Group(
                        align="flex-end",
                        gap="xs",
                        children=[dmc.Text(value, size="xl", fw=700), *delta_children],
                    ),
                    *sparkline_children,
                ],
            )
        )

    return cards


def build_category_bars_panel(
    data: DataFrame,
    metrics: list[tuple[str, str]],
    active_metric: str,
    panel_id: str = "category-bars",
) -> dmc.Paper:
    active_column = next((col for _, col in metrics if col == active_metric), metrics[0][1])
    data_frame = _ensure_dataframe(data)

    return dmc.Paper(
        p="md",
        withBorder=True,
        radius="md",
        children=[
            dmc.Group(
                justify="space-between",
                mb="sm",
                children=[
                    dmc.Text("By Category", fw=600, size="sm"),
                    dmc.SegmentedControl(
                        id=f"{panel_id}-toggle",
                        value=active_metric,
                        data=[{"label": label, "value": col} for label, col in metrics],
                        size="xs",
                        color="indigo",
                    ),
                ],
            ),
            dcc.Graph(
                id=f"{panel_id}-graph",
                figure=build_category_bars_chart(data_frame, value_column=active_column),
                config={"displayModeBar": False},
            ),
        ],
    )


def build_leaderboard(
    data: DataFrame,
    name_column: str = "SalesPerson",
    sales_column: str = "Revenue",
    margin_column: str = "MarginPct",
    target_column: str = "TargetPct",
    trend_column: str = "Trend",
) -> dmc.Stack:
    data_frame = _ensure_dataframe(data)
    if not _validate_chart_data(data_frame, {name_column, sales_column}):
        return dmc.Stack([dmc.Text("No data", c="dimmed")])

    has_margin = margin_column in data_frame.columns
    has_target = target_column in data_frame.columns
    has_trend = trend_column in data_frame.columns

    rows: list[Any] = []
    for rank, row_data in enumerate(data_frame.iter_rows(named=True), start=1):
        name = str(row_data[name_column])
        sales_val = float(row_data[sales_column] or 0)
        sales_fmt = f"${sales_val / 1e6:.1f}M" if sales_val >= 1e6 else f"${sales_val:,.0f}"

        margin_text = f"{float(row_data.get(margin_column) or 0):.1f}%" if has_margin else ""
        target_pct = float(row_data.get(target_column) or 0) if has_target else 0.0
        trend_val = float(row_data.get(trend_column) or 0) if has_trend else 0.0

        if target_pct >= 100:
            bar_color = DESIGN_TOKENS["pos"]
        elif target_pct >= 85:
            bar_color = DESIGN_TOKENS["accent"]
        else:
            bar_color = DESIGN_TOKENS["neg"]

        trend_color = DESIGN_TOKENS["pos"] if trend_val >= 0 else DESIGN_TOKENS["neg"]
        trend_arrow = "↑" if trend_val >= 0 else "↓"
        av_color = avatar_color(name)

        row_children: list[Any] = [
            dmc.Text(str(rank), fw=700, size="sm", w=20, ta="center", c="dimmed"),
            dmc.Avatar(
                initials(name),
                radius="xl",
                size="sm",
                style={"background": av_color, "color": "#fff", "fontWeight": 700},
            ),
            dmc.Box(
                style={"flex": 1},
                children=[dmc.Text(name, size="sm", fw=600, truncate="end")],
            ),
            dmc.Text(sales_fmt, size="sm", fw=600, w=60, ta="right"),
        ]

        if margin_text:
            row_children.append(dmc.Text(margin_text, size="xs", c="dimmed", w=40, ta="right"))

        if has_target:
            row_children.append(
                dmc.Box(
                    w=80,
                    children=[
                        dmc.Box(
                            style={
                                "background": COLORS["grid"],
                                "height": "5px",
                                "borderRadius": "2px",
                                "overflow": "hidden",
                            },
                            children=[
                                dmc.Box(
                                    style={
                                        "width": f"{min(target_pct, 100):.0f}%",
                                        "height": "100%",
                                        "background": bar_color,
                                        "borderRadius": "2px",
                                    }
                                )
                            ],
                        )
                    ],
                )
            )

        if has_trend:
            row_children.append(
                dmc.Text(
                    f"{trend_arrow}{abs(trend_val):.1f}%",
                    size="xs",
                    fw=600,
                    w=50,
                    ta="right",
                    style={"color": trend_color},
                )
            )

        rows.append(
            dmc.Group(
                gap="sm",
                align="center",
                wrap="nowrap",
                style={
                    "padding": "6px 0",
                    "borderBottom": f"1px solid {DESIGN_TOKENS['hairline']}",
                },
                children=row_children,
            )
        )

    return dmc.Stack(rows, gap=0)


def build_top_products_table(data: DataFrame) -> dag.AgGrid:
    data_frame = _ensure_dataframe(data)
    if data_frame.is_empty():
        return dag.AgGrid(columnDefs=[], rowData=[])

    # Registry uses 'Revenue' as the primary value column
    value_col = "Revenue"
    # Get values using protocol (replaces Polars-specific get_column().cast().drop_nulls().to_list())
    sales_list = [
        float(r.get(value_col, 0) or 0)
        for r in data_frame.iter_rows(named=True)
        if r.get(value_col) is not None
    ]
    max_sales = int(max(sales_list, default=0.0)) or 1

    return dag.AgGrid(
        id="product-table",
        columnDefs=[
            {"field": "Product", "filter": True, "sortable": True, "flex": 2},
            {"field": "Category", "filter": True, "sortable": True, "flex": 1},
            {
                "field": value_col,
                "headerName": "Sales",
                "filter": "agNumberColumnFilter",
                "sortable": True,
                "flex": 2,
                "cellRenderer": {
                    "function": (
                        "function(p){"
                        "var pct=Math.min(p.value/p.colDef.cellRendererParams.max*100,100);"
                        "var fmt=p.value>=1e6"
                        "?'$'+(p.value/1e6).toFixed(1)+'M'"
                        ":d3.format('$,.0f')(p.value);"
                        "return '<div style=\"display:flex;align-items:center;gap:6px;width:100%;padding:4px 0\">'+"
                        "'<div style=\"flex:1;background:#373a40;border-radius:2px;height:5px\">'+"
                        "'<div style=\"width:'+pct+'%;background:#6366F1;border-radius:2px;height:5px\"></div>'+"
                        "'</div><span>'+fmt+'</span></div>';}"
                    )
                },
                "cellRendererParams": {"max": max_sales},
            },
            {
                "field": "Profit",
                "filter": "agNumberColumnFilter",
                "sortable": True,
                "flex": 1,
                "valueFormatter": {"function": "d3.format('$,.0f')(params.value)"},
            },
        ],
        rowData=data_frame.to_dicts(),
        dashGridOptions={"theme": "themeQuartz"},
        style={"height": "400px", "width": "100%"},
    )
