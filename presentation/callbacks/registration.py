"""Callback Registration Facade.

Modularizes callback registration to reduce file complexity and improve maintainability.
(OO-001, CA-002)
"""

from dash import Dash

from domain import DataAnalysisExpressionsSourcePort
from domain import DataPort
from domain import QueryClientPort
from domain import TemplateLoaderPort

from .dashboard import register_dashboard_callbacks
from .dax import register_dax_callbacks
from .embed import register_embed_callbacks
from .inspector import register_inspector_callbacks
from .model import register_model_callbacks
from .navigation import register_navigation_callbacks


def register_callbacks(
    app: Dash,
    data: DataPort,
    data_analysis_expressions_query_source: DataAnalysisExpressionsSourcePort,
    client: QueryClientPort,
    loader: TemplateLoaderPort,
) -> None:
    """Register all dashboard callbacks by delegating to specialized modules. (OO-001)

    This facade maintains the original entry point for app.py while enforcing
    better separation of concerns by using narrow ports.

    Args:
        app: The Dash application instance.
        data: Port for fetching data.
        data_analysis_expressions_query_source: Port for DAX source and formatting.
        client: Port for executing raw queries.
        loader: Port for loading assets.
    """
    # 1. Navigation and Routing
    register_navigation_callbacks(app)

    # 2. DAX Inspection and Debugging
    register_inspector_callbacks(app, data_analysis_expressions_query_source)

    # 3. Main Dashboard Interactions
    register_dashboard_callbacks(app, data, data_analysis_expressions_query_source)

    # 4. DAX Query Page
    register_dax_callbacks(app, client)

    # 5. Embedded Reports
    register_embed_callbacks(app)

    # 6. Model Visualization
    register_model_callbacks(app, loader)
