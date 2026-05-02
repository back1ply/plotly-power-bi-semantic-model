"""Navigation Callbacks.

Handles active state management for the application's navigation components.
"""

from dash import Dash
from dash import Input
from dash import Output

from presentation.constants import ROUTE_DAX
from presentation.constants import ROUTE_EMBED
from presentation.constants import ROUTE_HOME
from presentation.constants import ROUTE_MODEL
from presentation.constants import ROUTE_SCHEMA
from presentation.helpers import safe_callback


def compute_active_nav(pathname: str) -> dict[str, bool]:
    """Return active state for each nav link based on current pathname. (API-003)"""
    return {
        "home": pathname == ROUTE_HOME,
        "schema": pathname == ROUTE_SCHEMA,
        "model": pathname == ROUTE_MODEL,
        "dax": pathname == ROUTE_DAX,
        "embed": pathname == ROUTE_EMBED,
    }


def register_navigation_callbacks(app: Dash) -> None:
    """Register callbacks for the navigation bar."""

    @app.callback(
        Output("nav-home", "active"),
        Output("nav-schema", "active"),
        Output("nav-model", "active"),
        Output("nav-dax", "active"),
        Output("nav-embed", "active"),
        Input("url", "pathname"),
    )
    @safe_callback
    def _update_active_nav(pathname: str) -> tuple[bool, bool, bool, bool, bool]:
        """Update active state of navigation links."""
        nav = compute_active_nav(pathname)
        return (
            nav["home"],
            nav["schema"],
            nav["model"],
            nav["dax"],
            nav["embed"],
        )
