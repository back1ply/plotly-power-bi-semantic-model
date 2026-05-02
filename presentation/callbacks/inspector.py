"""DAX Inspector Callbacks.

Handles logic for inspecting DAX queries behind dashboard charts.
"""

import logging

from dash import ALL
from dash import callback_context
from dash import Dash
from dash import Input
from dash import Output
from dash import State

from domain import DataAnalysisExpressionsSourcePort
from domain import QueryKey
from domain import QueryNotFoundError
from presentation.helpers import InspectorResult
from presentation.helpers import safe_callback


def handle_inspector_logic(
    chart_id: str,
    is_drawer_open: bool,
    repo: DataAnalysisExpressionsSourcePort,
    dynamic_dax: dict[str, str] | None = None,
) -> InspectorResult:
    """Business logic for the DAX inspector callback. (API-003)"""
    if not chart_id:
        return InspectorResult(is_drawer_open, "Select a chart to view its DAX query")

    try:
        # 1. Check if it's a dynamic chart and we have the DAX in store
        if chart_id == "custom_insights" and dynamic_dax and "dax" in dynamic_dax:
            return InspectorResult(not is_drawer_open, dynamic_dax["dax"])

        # 2. Otherwise handle standard startup queries
        try:
            query_key = QueryKey(chart_id)
            query = repo.get_raw_query(query_key)
        except ValueError:
            raise ValueError(f"Invalid query key: {chart_id}")

    except QueryNotFoundError:
        query = f"Query not found for: {chart_id}"
    except ValueError as exc:
        query = str(exc)
    except Exception as exc:
        logging.getLogger("callbacks").error("Inspector error: %s", exc)
        query = "Repository error"

    return InspectorResult(not is_drawer_open, query)


def register_inspector_callbacks(app: Dash, repo: DataAnalysisExpressionsSourcePort) -> None:
    """Register callbacks for the DAX inspector drawer."""

    @app.callback(
        Output("dax-inspector-drawer", "opened"),
        Output("dax-inspector-content", "children"),
        Input({"type": "open-dax-inspector", "chart": ALL}, "n_clicks"),
        State("dax-inspector-drawer", "opened"),
        State("dynamic-dax-store", "data"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _handle_inspector(
        n_clicks: list[int | None], is_drawer_open: bool, dynamic_dax: dict[str, str]
    ) -> tuple[bool, str]:
        """Toggle drawer and show DAX query for clicked chart."""
        if not any(n_clicks or []):
            return is_drawer_open, "Select a chart to view its DAX query"

        trigger_id = callback_context.triggered_id
        if not trigger_id:
            return is_drawer_open, "Select a chart to view its DAX query"

        chart_id = trigger_id.get("chart", "") if isinstance(trigger_id, dict) else ""

        result = handle_inspector_logic(chart_id, is_drawer_open, repo, dynamic_dax)
        return result.is_open, result.content
