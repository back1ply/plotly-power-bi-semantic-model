"""Callback Utilities.

Provides shared decorators for Dash callbacks.
"""

import functools
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import TypedDict

import pandas as pd
from dash import ALL
from dash import callback_context
from dash import Dash
from dash import dcc
from dash import Input
from dash import Output
from dash import State
from dash.exceptions import PreventUpdate

from domain import QueryKey
from domain import QueryNotFoundError
from domain import RepositoryPort
from domain import validate_dax_query
from presentation.charts import build_bar_chart
from presentation.charts import Orientation
from presentation.charts import SortOrder
from presentation.constants import NAV_ROUTES
from presentation.helpers import _inject_model_data
from presentation.helpers import _load_html_template
from presentation.helpers import create_empty_figure
from presentation.theme import CATEGORICAL_PALETTE


class ModelData(TypedDict):
    """Structure of model data for diagram visualization."""

    tables: list[dict[str, Any]]
    relationships: list[dict[str, Any]]


@dataclass(frozen=True)
class InspectorResult:
    """Encapsulates the result of the DAX inspector logic."""

    is_open: bool
    content: str


def safe_callback[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that logs callback crashes with full traceback.

    Wraps Dash callbacks to log any exceptions before re-raising.
    Useful for debugging production issues.

    Args:
        func: Callback function to wrap

    Returns:
        Wrapped function that logs errors before raising
    """
    _logger = logging.getLogger("callbacks")

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except Exception:
            _logger.exception("CALLBACK CRASH [%s]", func.__name__)
            raise

    return wrapper


def handle_inspector_logic(
    chart_id: str,
    is_drawer_open: bool,
    repo: RepositoryPort,
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
        # Validate that it's a valid query key before calling repo
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


def compute_active_nav(pathname: str) -> tuple[bool, bool, bool, bool, bool]:
    """Return active state for each nav link based on current pathname.

    Args:
        pathname: Current URL pathname from dcc.Location.

    Returns:
        Tuple of booleans (home, schema, model, dax, embed).
    """
    return (
        pathname == NAV_ROUTES[0],
        pathname == NAV_ROUTES[1],
        pathname == NAV_ROUTES[2],
        pathname == NAV_ROUTES[3],
        pathname == NAV_ROUTES[4],
    )


def register_callbacks(app: Dash, repo: RepositoryPort) -> None:
    """Register all dashboard callbacks with explicit dependency injection.

    Args:
        app: The Dash application instance.
        repo: The dashboard repository for data access.
    """

    @app.callback(
        Output("nav-home", "active"),
        Output("nav-schema", "active"),
        Output("nav-model", "active"),
        Output("nav-dax", "active"),
        Output("nav-embed", "active"),
        Input("url", "pathname"),
    )
    def _update_active_nav(pathname: str) -> tuple[bool, bool, bool, bool, bool]:
        return compute_active_nav(pathname)

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

        # Use the modern triggered_id property for reliable ID retrieval (Dash 2.4+)
        trigger_id = callback_context.triggered_id
        if not trigger_id:
            return is_drawer_open, "Select a chart to view its DAX query"

        # Extract the 'chart' key if it's a pattern-matching dictionary ID
        chart_id = trigger_id.get("chart", "") if isinstance(trigger_id, dict) else ""

        result = handle_inspector_logic(chart_id, is_drawer_open, repo, dynamic_dax)
        return result.is_open, result.content

    @app.callback(
        Output("home-builder-graph", "figure"),
        Output("dynamic-dax-store", "data"),
        Input("home-builder-measure", "value"),
        Input("home-builder-dimension", "value"),
    )
    @safe_callback
    def _update_custom_chart(measure_label: str, dimension_label: str):
        """Callback to update the custom chart on home page and store its DAX."""
        if not measure_label or not dimension_label:
            return create_empty_figure("Select options"), {}

        try:
            # 1. Fetch data using encapsulated repository method
            df = repo.get_summarized_data(
                measure_key=measure_label, dimension_key=dimension_label
            )

            if df.empty:
                return create_empty_figure("No data returned"), {}

            # Identify columns - dimension is first, measure is second
            dim_col = str(df.columns[0])
            val_col = str(df.columns[1])

            fig = build_bar_chart(
                df,
                dim_col,
                val_col,
                color=CATEGORICAL_PALETTE,
                orientation=Orientation.HORIZONTAL,
                sort_order=SortOrder.DESCENDING,
            )
            fig.update_layout(title=f"{measure_label} by {dimension_label}")

            # 2. Prepare DAX for the store - using encapsulated repository method
            dax = repo.get_summarized_query_text(
                measure_key=measure_label, dimension_key=dimension_label
            )

            return fig, {"dax": dax}

        except Exception as exc:
            return create_empty_figure(f"Error: {exc}"), {"error": str(exc)}

    @app.callback(
        Output("model-diagram-frame", "srcDoc"),
        Input("model-data-store", "data"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _update_diagram(model_data: dict) -> str:
        """Update the iframe when model data changes."""
        html_template = _load_html_template()
        return _inject_model_data(html_template, model_data)

    _register_dax_callbacks(app, repo)
    _register_embed_callbacks(app)


def _register_embed_callbacks(app: Dash) -> None:
    """Register clientside callbacks for Power BI embedding."""
    app.clientside_callback(
        """
        function(n_clicks, pathname) {
            if (pathname !== "/embed") return window.dash_clientside.no_update;
            
            // Call the global init function defined in embed_init.js
            if (window._pbiInitEmbed) {
                window._pbiInitEmbed(true); // true = force reload
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("pbi-embed-trigger", "data"),
        Input("pbi-embed-reload", "n_clicks"),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )


def _register_dax_callbacks(app: Dash, repo: RepositoryPort) -> None:
    """Register all DAX Query page callbacks."""

    @app.callback(
        Output("dax-query-results", "rowData"),
        Output("dax-query-results", "columnDefs"),
        Output("dax-query-status", "children"),
        Input("dax-query-execute", "n_clicks"),
        State("dax-query-input", "data"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _execute_dax_query(_: int, dax: str | None) -> tuple[list, list, str]:
        """Execute a DAX query against the semantic model and return results."""
        if not dax or not dax.strip():
            return [], [], "No query entered"

        error = validate_dax_query(dax)
        if error:
            return [], [], f"✗ {error}"

        t0 = time.perf_counter()
        try:
            # Use the repository directly instead of current_app.config (CA-002)
            rows = repo.query(dax.strip())
            elapsed = time.perf_counter() - t0

            if not rows:
                return [], [], f"✓ 0 rows · {elapsed:.2f}s"

            columns = list(rows[0].keys())
            col_defs = [{"field": col, "headerName": col} for col in columns]
            return (
                rows,
                col_defs,
                f"✓ {len(rows):,} rows · {len(columns)} cols · {elapsed:.2f}s",
            )

        except Exception as exc:
            return [], [], f"✗ {exc}"

    # Store → Monaco: sync external writes back into editor
    app.clientside_callback(
        """
        function(data) {
            if (window._updateMonacoFromExternal) {
                window._updateMonacoFromExternal(data);
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("dax-editor-sync-ack", "data", allow_duplicate=True),
        Input("dax-query-input", "data"),
        prevent_initial_call=True,
    )

    # Schema-insert: insert clicked field expression at Monaco cursor position
    app.clientside_callback(
        """
        function(nClicks, ids, currentValue) {
            const ctx = window.dash_clientside.callback_context;
            if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
                return window.dash_clientside.no_update;
            }
            const anyClicked = nClicks && nClicks.some(function(n) { return n && n > 0; });
            if (!anyClicked) return window.dash_clientside.no_update;

            const propId = ctx.triggered[0].prop_id;
            const idStr = propId.substring(0, propId.lastIndexOf('.'));
            let expr = '';
            try { expr = JSON.parse(idStr).expr; } catch(e) {
                return window.dash_clientside.no_update;
            }
            if (!expr) return window.dash_clientside.no_update;

            const editor = window._dashMonacoEditor;
            if (editor) {
                const selection = editor.getSelection();
                const model = editor.getModel();
                const lineContent = model.getLineContent(selection.startLineNumber);
                const before = lineContent.substring(0, selection.startColumn - 1);
                const sep = (before && !/[ \\n]$/.test(before)) ? ' ' : '';
                editor.executeEdits('schema-insert', [{
                    range: selection,
                    text: sep + expr,
                    forceMoveMarkers: true,
                }]);
                editor.focus();
                return editor.getValue();
            }
            const val = currentValue || '';
            const sep = (val && !/[ \\n]$/.test(val)) ? ' ' : '';
            return val + sep + expr;
        }
        """,
        Output("dax-query-input", "data", allow_duplicate=True),
        Input({"type": "schema-insert", "expr": ALL}, "n_clicks"),
        State({"type": "schema-insert", "expr": ALL}, "id"),
        State("dax-query-input", "data"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("dax-query-input", "data", allow_duplicate=True),
        Input("dax-query-clear", "n_clicks"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _clear_dax_query(_: int) -> str:
        """Clear the DAX editor content."""
        return ""

    # Add clientside formatting and copy logic
    app.clientside_callback(
        """
        function(n_format, n_copy, current_dax) {
            const ctx = window.dash_clientside.callback_context;
            if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
            
            const trigger_id = ctx.triggered[0].prop_id.split('.')[0];
            
            if (trigger_id === 'dax-query-format') {
                if (!current_dax) return [window.dash_clientside.no_update, window.dash_clientside.no_update];
                // Simple heuristic DAX formatter
                let formatted = current_dax
                    .replace(/\\s+/g, ' ')
                    .replace(/\\s*([,()])\\s*/g, '$1 ')
                    .replace(/\\((?=[^\\)]*\\()/g, '(\\n  ')
                    .replace(/\\)/g, '\\n)')
                    .trim();
                return [formatted, window.dash_clientside.no_update];
            }
            
            if (trigger_id === 'dax-query-copy') {
                if (current_dax) {
                    navigator.clipboard.writeText(current_dax);
                }
                return [window.dash_clientside.no_update, "Copied!"];
            }
            
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        """,
        Output("dax-query-input", "data", allow_duplicate=True),
        Output("dax-query-status", "children", allow_duplicate=True),
        Input("dax-query-format", "n_clicks"),
        Input("dax-query-copy", "n_clicks"),
        State("dax-query-input", "data"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("dax-query-download", "data"),
        Input("dax-query-export", "n_clicks"),
        State("dax-query-results", "rowData"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _export_dax_results(_: int, row_data: list[dict[str, Any]] | None) -> dict[str, Any]:
        """Export grid row data as a downloadable CSV file."""
        if not row_data:
            raise PreventUpdate
        df = pd.DataFrame(row_data)
        return dcc.send_data_frame(df.to_csv, "query_results.csv", index=False)

    @app.callback(
        Output("dax-query-export", "disabled"),
        Input("dax-query-results", "rowData"),
    )
    @safe_callback
    def _toggle_export_button(row_data: list[dict[str, Any]] | None) -> bool:
        """Disable Export CSV button when grid has no data."""
        return not bool(row_data)

    # Schema autocomplete: register Monaco completion provider when schema loads
    app.clientside_callback(
        """
        function(schemaData) {
            if (!schemaData || !schemaData.tables) return window.dash_clientside.no_update;
            window._daxSchemaData = schemaData;
            return window.dash_clientside.no_update;
        }
        """,
        Output("dax-editor-sync-ack", "data", allow_duplicate=True),
        Input("dax-schema-store", "data"),
        prevent_initial_call="initial_duplicate",
    )
