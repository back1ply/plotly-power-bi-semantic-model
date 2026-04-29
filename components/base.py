"""Base UI Components and Layout.

Provides shared UI components for the dashboard.
"""

from dataclasses import dataclass

import dash_mantine_components as dmc
from dash_iconify import DashIconify

from domain import QueryKey
from presentation.constants import ROUTE_DAX
from presentation.constants import ROUTE_EMBED
from presentation.constants import ROUTE_HOME
from presentation.constants import ROUTE_MODEL
from presentation.constants import ROUTE_SCHEMA


@dataclass(frozen=True)
class ConnectionState:
    has_credentials: bool = False
    errors: dict[str, str] | None = None


def build_sidebar(state: ConnectionState, app_title: str = "Sales Dashboard") -> dmc.Flex:
    """Create dashboard sidebar navigation with compact connection status.

    Args:
        state: The current connection state to Power BI.
        app_title: Display name shown at the top of the sidebar.

    Returns:
        Mantine Flex column containing nav links and connection status.
    """
    if state.has_credentials and not state.errors:
        status_color = "green"
        status_label = "Connected to Power BI"
    elif state.has_credentials and state.errors:
        status_color = "yellow"
        status_label = "Partial connection"
    else:
        status_color = "red"
        status_label = "Power BI unavailable"

    connection_status = dmc.Group(
        gap="xs",
        mt="auto",
        pt="md",
        style={"borderTop": "1px solid var(--mantine-color-dark-4)"},
        children=[
            DashIconify(
                icon="tabler:circle-filled",
                width=8,
                color=f"var(--mantine-color-{status_color}-5)",
            ),
            dmc.Text(status_label, size="xs", c="dimmed"),
        ],
    )

    return dmc.Flex(
        direction="column",
        h="100%",
        gap="xs",
        children=[
            dmc.Title(app_title, order=4, mb="xl", fw=700),
            dmc.NavLink(
                id="nav-home",
                label="Executive Summary",
                href=ROUTE_HOME,
                leftSection=DashIconify(icon="tabler:dashboard"),
                active=False,
                variant="subtle",
                color="blue",
            ),
            dmc.NavLink(
                id="nav-schema",
                label="Data Model Schema",
                href=ROUTE_SCHEMA,
                leftSection=DashIconify(icon="tabler:database"),
                active=False,
                variant="subtle",
                color="blue",
            ),
            dmc.NavLink(
                id="nav-model",
                label="Model Diagram",
                href=ROUTE_MODEL,
                leftSection=DashIconify(icon="tabler:topology-star"),
                active=False,
                variant="subtle",
                color="blue",
            ),
            dmc.NavLink(
                id="nav-dax",
                label="DAX Query",
                href=ROUTE_DAX,
                leftSection=DashIconify(icon="tabler:terminal-2"),
                active=False,
                variant="subtle",
                color="blue",
            ),
            dmc.NavLink(
                id="nav-embed",
                label="PBI Report",
                href=ROUTE_EMBED,
                leftSection=DashIconify(icon="tabler:chart-bar"),
                active=False,
                variant="subtle",
                color="violet",
            ),
            connection_status,
        ],
    )


def build_dax_inspector_button(query_key: QueryKey | str) -> dmc.ActionIcon:
    """Create button to open DAX inspector for a chart.

    Args:
        query_key: Cache key identifier for the chart

    Returns:
        Mantine ActionIcon that triggers inspector drawer
    """
    return dmc.ActionIcon(
        DashIconify(icon="tabler:code", width=20),
        id={"type": "open-dax-inspector", "chart": query_key},
        variant="subtle",
        size="lg",
    )


def build_dax_inspector_drawer() -> dmc.Drawer:
    """Create drawer component for viewing DAX queries.

    Returns:
        Mantine Drawer that displays DAX query code when triggered
    """
    return dmc.Drawer(
        id="dax-inspector-drawer",
        title="DAX Inspector",
        position="right",
        size="40%",
        opened=False,
        children=[
            dmc.Code(
                id="dax-inspector-content",
                block=True,
                children="Select a chart to view its DAX query",
            )
        ],
    )
