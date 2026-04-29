"""Layout.

Provides the main application layout and structure.
"""

import dash_mantine_components as dmc
from dash import dcc
from dash import html
from dash import page_container

from components.base import build_dax_inspector_drawer
from components.base import build_sidebar
from components.base import ConnectionState
from config import ThemeConfig


def create_layout(
    has_credentials: bool,
    connection_errors: dict[str, str],
    theme: ThemeConfig | None = None,
) -> dmc.MantineProvider:
    """Create the main Dash application layout."""
    if theme is None:
        theme = ThemeConfig()
    state = ConnectionState(has_credentials=has_credentials, errors=connection_errors)
    return dmc.MantineProvider(
        forceColorScheme="dark",
        theme={"fontFamily": theme.font_family, "primaryColor": theme.primary_color},
        children=html.Div(
            [
                dcc.Location(id="url", refresh=False),
                dcc.Store(id="dynamic-dax-store", data={}),
                dcc.Store(id="model-data-store", data={}),
                dmc.AppShell(
                    header={"height": 0},
                    navbar={"width": 300, "breakpoint": "sm", "collapsed": {"mobile": True}},
                    padding="xl",
                    children=[
                        dmc.AppShellNavbar(
                            p="md",
                            children=[build_sidebar(state, app_title=theme.app_title)],
                        ),
                        dmc.AppShellMain(
                            children=[
                                page_container,
                                build_dax_inspector_drawer(),
                            ]
                        ),
                    ],
                ),
            ]
        ),
    )
