"""DAX Query Callbacks.

Handles execution and management of raw DAX queries from the editor.
"""

import csv
import io
import time
from typing import Any

from dash import ALL
from dash import Dash
from dash import dcc
from dash import Input
from dash import Output
from dash import State
from dash.exceptions import PreventUpdate

from domain import clean_dax_query
from domain import QueryClientPort
from domain import validate_dax_query
from presentation.helpers import safe_callback


def register_dax_callbacks(app: Dash, client: QueryClientPort) -> None:
    """Register all DAX Query page callbacks."""

    @app.callback(
        Output("dax-query-results", "rowData"),
        Output("dax-query-results", "columnDefs"),
        Output("dax-query-status", "children", allow_duplicate=True),
        Input("dax-query-execute", "n_clicks"),
        State("dax-editor", "value"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _execute_dax_query(_: int, dax_query_text: str | None) -> tuple[list, list, str]:
        """Execute a DAX query against the semantic model and return results."""
        cleaned_query = clean_dax_query(dax_query_text)
        if not cleaned_query:
            return [], [], "No query entered"

        error = validate_dax_query(cleaned_query)
        if error:
            return [], [], f"✗ {error}"

        start_time = time.perf_counter()
        try:
            data_frame = client.query(cleaned_query)
            elapsed = time.perf_counter() - start_time

            if data_frame.is_empty():
                return [], [], f"✓ 0 rows · {elapsed:.2f}s"

            columns = data_frame.columns
            column_definitions = [{"field": column, "headerName": column} for column in columns]
            # Convert to list of dicts for AG Grid
            rows = data_frame.to_dicts()
            return (
                rows,
                column_definitions,
                f"✓ {len(rows):,} rows · {len(columns)} cols · {elapsed:.2f}s",
            )

        except Exception as exception:
            return [], [], f"✗ {exception}"

    @app.callback(
        Output("dax-editor", "value", allow_duplicate=True),
        Output("dax-query-status", "children", allow_duplicate=True),
        Input("dax-query-clear", "n_clicks"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _clear_dax_query(_: int) -> tuple[str, str]:
        """Clear the DAX editor content and reset status."""
        return "", "Ready"

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
                // Slightly smarter heuristic DAX formatter
                let formatted = current_dax
                    .replace(/\\s*,\\s*/g, ',\\n    ')
                    .replace(/\\s*\\(\\s*/g, '(\\n    ')
                    .replace(/\\s*\\)\\s*/g, '\\n)')
                    .replace(/(EVALUATE|DEFINE|MEASURE|VAR|RETURN)/gi, '\\n$1')
                    .trim();
                return [formatted, "✓ Formatted"];
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
        Output("dax-editor", "value", allow_duplicate=True),
        Output("dax-query-status", "children", allow_duplicate=True),
        Input("dax-query-format", "n_clicks"),
        Input("dax-query-copy", "n_clicks"),
        State("dax-editor", "value"),
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

        output = io.StringIO()
        if row_data:
            writer = csv.DictWriter(output, fieldnames=row_data[0].keys())
            writer.writeheader()
            writer.writerows(row_data)

        return dcc.send_bytes(output.getvalue().encode(), "query_results.csv")

    @app.callback(
        Output("dax-query-export", "disabled"),
        Input("dax-query-results", "rowData"),
    )
    @safe_callback
    def _toggle_export_button(row_data: list[dict[str, Any]] | None) -> bool:
        """Disable Export CSV button when grid has no data."""
        return not bool(row_data)

    app.clientside_callback(
        """
        function(schemaData) {
            if (!schemaData || !schemaData.tables) return window.dash_clientside.no_update;
            window._daxSchemaData = schemaData;
            return window.dash_clientside.no_update;
        }
        """,
        Output("dax-schema-ack", "data"),
        Input("dax-schema-store", "data"),
        prevent_initial_call=False,
    )

    app.clientside_callback(
        """
        function(nClicks) {
            var ctx = window.dash_clientside.callback_context;
            if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
                return window.dash_clientside.no_update;
            }
            var anyClicked = nClicks && nClicks.some(function(n) { return n && n > 0; });
            if (!anyClicked) return window.dash_clientside.no_update;

            var propId = ctx.triggered[0].prop_id;
            var idStr = propId.substring(0, propId.lastIndexOf('.'));
            var expr = '';
            try { expr = JSON.parse(idStr).expr; } catch(e) {
                return window.dash_clientside.no_update;
            }
            if (!expr || !window._daxEditorInsert) return window.dash_clientside.no_update;
            window._daxEditorInsert(expr);
            return window.dash_clientside.no_update;
        }
        """,
        Output("dax-schema-ack", "data", allow_duplicate=True),
        Input({"type": "schema-insert", "expr": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
