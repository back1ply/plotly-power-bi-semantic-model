"""Model Diagram Callbacks.

Handles updating the interactive model diagram when underlying data changes.
"""

from dash import Dash
from dash import Input
from dash import Output

from domain import TemplateLoaderPort
from presentation.helpers import inject_model_data
from presentation.helpers import load_html_template
from presentation.helpers import safe_callback


def register_model_callbacks(app: Dash, loader: TemplateLoaderPort) -> None:
    """Register callbacks for the model diagram view."""

    @app.callback(
        Output("model-diagram-frame", "srcDoc"),
        Input("model-data-store", "data"),
        prevent_initial_call=True,
    )
    @safe_callback
    def _update_diagram(model_data: dict) -> str:
        """Update the iframe when model data changes."""
        html_template = load_html_template(loader)
        return inject_model_data(html_template, model_data)
