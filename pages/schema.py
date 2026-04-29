"""Data Model Schema Page.

Displays the Power BI semantic model schema including tables, columns, and measures
using an interactive accordion view.
"""

import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from domain import ModelSchema
from domain import QueryError
from domain import SchemaPort
from presentation.dependency import get_repository

# Register page at module level (Standard Dash Pages pattern)
dash.register_page(
    __name__,
    path="/schema",
    name="Data Model Schema",
    order=2,
)


def _build_schema_accordion(schema: ModelSchema) -> dmc.Accordion:
    """Build the accordion items for each table in the schema."""
    items = []
    for table_name, table in schema.tables.items():
        columns = table.columns
        measures = table.measures

        # Build panel content
        content = []

        if columns:
            content.append(dmc.Text("Columns", fw=600, size="sm", mb=5, c="blue"))
            content.append(
                dmc.Group(
                    gap="xs",
                    mb="md",
                    children=[dmc.Badge(col, variant="outline", size="sm") for col in columns],
                )
            )

        if measures:
            content.append(dmc.Text("Measures", fw=600, size="sm", mb=5, c="teal"))
            content.append(
                dmc.Group(
                    gap="xs",
                    children=[
                        dmc.Badge(m, variant="light", color="teal", size="sm") for m in measures
                    ],
                )
            )

        if not columns and not measures:
            content.append(dmc.Text("No columns or measures found.", size="sm", c="dimmed"))

        items.append(
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        dmc.Group(
                            children=[
                                DashIconify(icon="tabler:table", width=20, color="gray"),
                                dmc.Text(table_name, fw=500),
                            ]
                        )
                    ),
                    dmc.AccordionPanel(dmc.Stack(children=content)),
                ],
                value=table_name,
            )
        )

    return dmc.Accordion(children=items, variant="separated", chevronPosition="right")


def layout() -> dmc.Stack | dmc.Alert:
    """Create the schema page layout by fetching data from repository."""
    repo = get_repository(SchemaPort)
    return serve_layout(repo)


def serve_layout(repo: SchemaPort) -> dmc.Stack | dmc.Alert:
    """Logic to build the layout, separated for testability. (CA-003)"""
    try:
        schema_data = repo.get_schema()
    except QueryError as exc:
        return dmc.Alert(
            f"Failed to load model schema: {exc}",
            title="Schema Fetch Error",
            color="red",
            variant="filled",
            icon=DashIconify(icon="tabler:alert-circle"),
            mt="xl",
        )

    return dmc.Stack(
        gap="xl",
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Stack(
                        gap=0,
                        children=[
                            dmc.Title("Data Model Schema", order=3, fw=700),
                            dmc.Text(
                                "Explore the tables, columns, and measures in your semantic model.",
                                size="sm",
                                c="dimmed",
                            ),
                        ],
                    ),
                ],
            ),
            _build_schema_accordion(schema_data),
        ],
    )
