"""PBI Embedded Report Page (PoC).

Renders the AdventureWorks Power BI report inside the Dash shell
using the app-owns-data embedding flow.
"""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash import html

dash.register_page(
    __name__,
    path="/embed",
    name="PBI Report",
    order=5,
)

def layout() -> dmc.Stack:
    """Return the PBI Embedded report page layout."""
    return dmc.Stack(
        gap="md",
        p="md",
        style={"height": "calc(100vh - 100px)"},
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Stack(
                        gap=0,
                        children=[
                            dmc.Title("AdventureWorks Report", order=3, fw=700),
                            dmc.Text(
                                "Native Power BI embedding via Service Principal",
                                size="sm",
                                c="dimmed",
                            ),
                        ],
                    ),
                    dmc.Group(
                        children=[
                            dmc.Button(
                                "Reload Report",
                                id="pbi-embed-reload",
                                variant="outline",
                                size="xs",
                                leftSection=dmc.ThemeIcon(
                                    html.I(className="tabler:refresh"),
                                    size="xs",
                                    variant="transparent"
                                ),
                            ),
                            dmc.ActionIcon(
                                html.I(className="tabler:maximize"),
                                id="pbi-embed-maximize",
                                variant="subtle",
                                color="gray",
                            ),
                        ]
                    ),
                ],
            ),
            dmc.Paper(
                withBorder=True,
                radius="md",
                shadow="sm",
                style={"flex": 1, "position": "relative", "overflow": "hidden"},
                children=[
                    dmc.LoadingOverlay(
                        visible=False,
                        id="pbi-embed-loading",
                        overlayProps={"blur": 2},
                    ),
                    html.Div(
                        id="embed-container",
                        style={
                            "width": "100%",
                            "height": "100%",
                            "minHeight": "600px",
                        },
                    ),
                ],
            ),
            # Trigger store to force re-init
            dcc.Store(id="pbi-embed-trigger", data=0),
        ],
    )
