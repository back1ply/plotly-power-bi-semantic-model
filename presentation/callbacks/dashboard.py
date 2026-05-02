"""Dashboard Callbacks.

Handles interactive chart building and dynamic data visualization on the home page.
"""

from dash import Dash
from dash import Input
from dash import Output

from domain import DataPort
from domain import DataAnalysisExpressionsSourcePort
from presentation.builders.constants import Orientation
from presentation.builders.constants import SortOrder
from presentation.builders.figures import build_bar_chart
from presentation.helpers import create_empty_figure
from presentation.helpers import safe_callback
from presentation.theme import CATEGORICAL_PALETTE


def register_dashboard_callbacks(app: Dash, data_repo: DataPort, dax_repo: DataAnalysisExpressionsSourcePort) -> None:
    """Register callbacks for the home page dashboard builder."""

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
            # 1. Fetch data using encapsulated DataPort method
            data_frame = data_repo.get_summarized_data(
                measure_key=measure_label, dimension_key=dimension_label
            )

            if data_frame.is_empty():
                return create_empty_figure("No data returned"), {}

            dimension_column = str(data_frame.columns[0])
            measure_column = str(data_frame.columns[1])

            fig = build_bar_chart(
                data_frame,
                dimension_column,
                measure_column,
                color=CATEGORICAL_PALETTE,
                orientation=Orientation.HORIZONTAL,
                sort_order=SortOrder.DESCENDING,
            )
            fig.update_layout(title=f"{measure_label} by {dimension_label}")

            # 2. Prepare DAX for the store using DaxSourcePort
            dax_query = dax_repo.get_summarized_query_text(
                measure_key=measure_label, dimension_key=dimension_label
            )

            return fig, {"dax": dax_query}

        except Exception as exception:
            return create_empty_figure(f"Error: {exception}"), {"error": str(exception)}
