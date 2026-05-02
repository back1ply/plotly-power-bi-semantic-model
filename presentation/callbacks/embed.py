"""Power BI Embed Callbacks.

Handles clientside initialization of the Power BI report embed container.
"""

from dash import Dash
from dash import Input
from dash import Output


def register_embed_callbacks(app: Dash) -> None:
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
