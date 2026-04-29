"""DAX Query View Page.

Provides an interactive DAX query editor connected live to the semantic model.
Features include syntax highlighting, autocomplete, and a field explorer.
"""

import dash
import dash_ace
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import State
from dash_iconify import DashIconify

from domain import QueryError
from domain import SchemaPort
from presentation.dependency import get_repository

dash.register_page(
    __name__,
    path="/dax",
    name="DAX Query",
    order=4,
)


def _serialize_schema(schema) -> dict:
    """Convert schema object to JSON-serializable dict for dcc.Store."""
    return {
        "tables": [
            {
                "name": table_name,
                "columns": list(table.columns),
                "measures": list(table.measures),
            }
            for table_name, table in schema.tables.items()
        ]
    }


def _build_schema_panel(schema, search_term: str = "") -> dmc.ScrollArea:
    """Build the schema field tree panel from a loaded schema object."""
    items = []
    search_lower = search_term.lower()

    for table_name, table in schema.tables.items():
        # Filter logic
        filtered_cols = [
            c
            for c in table.columns
            if search_lower in c.lower() or search_lower in table_name.lower()
        ]
        filtered_measures = [
            m
            for m in table.measures
            if search_lower in m.lower() or search_lower in table_name.lower()
        ]

        if search_term and not filtered_cols and not filtered_measures:
            continue

        content = []
        if filtered_cols:
            content.append(dmc.Text("Columns", size="xs", c="dimmed", mb=4))
            content.append(
                dmc.Flex(
                    wrap="wrap",
                    gap=4,
                    mb="xs",
                    children=[
                        html.Span(
                            dmc.Badge(col, size="xs", variant="outline"),
                            id={
                                "type": "schema-insert",
                                "expr": f"'{table_name}'[{col}]",
                            },
                            n_clicks=0,
                            style={"cursor": "pointer"},
                        )
                        for col in filtered_cols
                    ],
                )
            )

        if filtered_measures:
            content.append(dmc.Text("Measures", size="xs", c="dimmed", mb=4))
            content.append(
                dmc.Flex(
                    wrap="wrap",
                    gap=4,
                    children=[
                        html.Span(
                            dmc.Badge(m, size="xs", variant="light", color="teal"),
                            id={"type": "schema-insert", "expr": f"[{m}]"},
                            n_clicks=0,
                            style={"cursor": "pointer"},
                        )
                        for m in filtered_measures
                    ],
                )
            )

        items.append(
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        dmc.Group(
                            gap="xs",
                            children=[
                                DashIconify(icon="tabler:table", width=14, color="gray"),
                                dmc.Text(table_name, size="sm"),
                            ],
                        )
                    ),
                    dmc.AccordionPanel(dmc.Stack(gap=4, children=content)),
                ],
                value=table_name,
            )
        )

    if not items:
        return dmc.Center(dmc.Text("No fields match your search", size="sm", c="dimmed", py="xl"))

    return dmc.ScrollArea(
        h="calc(100vh - 280px)",
        type="auto",
        children=dmc.Accordion(
            children=items,
            variant="filled",
            chevronPosition="right",
        ),
    )


def layout():
    """Return the DAX Query page layout."""
    repo = get_repository(SchemaPort)
    return serve_layout(repo)


def serve_layout(repo: SchemaPort):
    """Build and return the full DAX Query page layout with live schema data."""
    try:
        schema = repo.get_schema()
    except QueryError as exc:
        return dmc.Alert(
            f"Failed to load schema: {exc}",
            title="Schema Error",
            color="red",
            variant="filled",
            icon=DashIconify(icon="tabler:alert-circle"),
            mt="xl",
        )

    schema_data = _serialize_schema(schema)

    return dmc.Stack(
        gap="md",
        p="md",
        style={"height": "calc(100vh - 80px)"},
        children=[
            # Hidden state stores
            html.Div(
                style={"display": "none"},
                children=[
                    dcc.Store(id="dax-schema-store", data=schema_data),
                    dcc.Store(id="dax-schema-ack", data=0),
                    dcc.Download(id="dax-query-download"),
                ],
            ),
            dmc.Grid(
                gutter="md",
                style={"flex": 1},
                children=[
                    # Left: Field Explorer
                    dmc.GridCol(
                        span=3,
                        style={"height": "100%"},
                        children=dmc.Paper(
                            p="sm",
                            withBorder=True,
                            radius="md",
                            style={"height": "100%", "display": "flex", "flexDirection": "column"},
                            children=[
                                dmc.Group(
                                    mb="xs",
                                    gap="xs",
                                    children=[
                                        DashIconify(icon="tabler:database", width=18, color="blue"),
                                        dmc.Text("Model Explorer", fw=700, size="sm"),
                                    ],
                                ),
                                dmc.TextInput(
                                    id="dax-schema-search",
                                    placeholder="Search tables or fields...",
                                    leftSection=DashIconify(icon="tabler:search", width=14),
                                    size="xs",
                                    mb="sm",
                                ),
                                html.Div(
                                    id="dax-schema-panel-container",
                                    style={"flex": 1},
                                    children=_build_schema_panel(schema),
                                ),
                                dmc.Text(
                                    "Click to insert at cursor",
                                    size="xs",
                                    c="dimmed",
                                    mt="xs",
                                    fs="italic",
                                    ta="center",
                                ),
                            ],
                        ),
                    ),
                    # Right: Editor and Results
                    dmc.GridCol(
                        span=9,
                        children=dmc.Stack(
                            gap="md",
                            style={"height": "100%"},
                            children=[
                                # Query Editor
                                dmc.Paper(
                                    p="sm",
                                    withBorder=True,
                                    radius="md",
                                    children=[
                                        dmc.Group(
                                            justify="space-between",
                                            mb="xs",
                                            children=[
                                                dmc.Group(
                                                    gap="xs",
                                                    children=[
                                                        dmc.Button(
                                                            "Execute",
                                                            id="dax-query-execute",
                                                            leftSection=DashIconify(
                                                                icon="tabler:player-play-filled"
                                                            ),
                                                            size="sm",
                                                            color="blue",
                                                        ),
                                                        dmc.Button(
                                                            "Format",
                                                            id="dax-query-format",
                                                            variant="light",
                                                            leftSection=DashIconify(
                                                                icon="tabler:align-left"
                                                            ),
                                                            size="sm",
                                                            color="gray",
                                                        ),
                                                        dmc.Button(
                                                            "Copy",
                                                            id="dax-query-copy",
                                                            variant="subtle",
                                                            leftSection=DashIconify(
                                                                icon="tabler:copy"
                                                            ),
                                                            size="sm",
                                                            color="gray",
                                                        ),
                                                        dmc.Button(
                                                            "Clear",
                                                            id="dax-query-clear",
                                                            variant="subtle",
                                                            leftSection=DashIconify(
                                                                icon="tabler:trash"
                                                            ),
                                                            size="sm",
                                                            color="red",
                                                        ),
                                                    ],
                                                ),
                                                dmc.Text(
                                                    id="dax-query-status",
                                                    size="xs",
                                                    c="dimmed",
                                                    children="Ready",
                                                ),
                                            ],
                                        ),
                                        dash_ace.DashAceEditor(
                                            id="dax-editor",
                                            value="",
                                            mode="dax",
                                            theme="monokai",
                                            tabSize=4,
                                            enableBasicAutocompletion=True,
                                            enableLiveAutocompletion=True,
                                            placeholder='EVALUATE\n    ROW("Value", 1)',
                                            style={
                                                "height": "350px",
                                                "width": "100%",
                                                "fontSize": "14px",
                                            },
                                        ),
                                    ],
                                ),
                                # Results
                                dmc.Paper(
                                    p=0,
                                    withBorder=True,
                                    radius="md",
                                    style={
                                        "flex": 1,
                                        "overflow": "hidden",
                                        "display": "flex",
                                        "flexDirection": "column",
                                    },
                                    children=[
                                        dmc.Group(
                                            p="xs",
                                            justify="space-between",
                                            style={
                                                "borderBottom": "1px solid var(--mantine-color-dark-4)"
                                            },
                                            children=[
                                                dmc.Text("Query Results", fw=600, size="sm"),
                                                dmc.Button(
                                                    "Export CSV",
                                                    id="dax-query-export",
                                                    variant="subtle",
                                                    size="xs",
                                                    leftSection=DashIconify(icon="tabler:download"),
                                                    disabled=True,
                                                ),
                                            ],
                                        ),
                                        dcc.Loading(
                                            type="circle",
                                            children=dag.AgGrid(
                                                id="dax-query-results",
                                                rowData=[],
                                                columnDefs=[],
                                                defaultColDef={
                                                    "resizable": True,
                                                    "sortable": True,
                                                    "filter": True,
                                                    "minWidth": 120,
                                                },
                                                dashGridOptions={
                                                    "domLayout": "normal",
                                                    "pagination": True,
                                                    "paginationPageSize": 100,
                                                },
                                                style={"height": "100%", "width": "100%"},
                                                className="ag-theme-alpine-dark",
                                            ),
                                            style={"height": "100%"},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


# Search callback for schema explorer
@dash.callback(
    Output("dax-schema-panel-container", "children"),
    Input("dax-schema-search", "value"),
    State("dax-schema-store", "data"),
    prevent_initial_call=True,
)
def search_schema(search_term: str, schema_data: dict):
    """Filter the schema accordion based on search term."""
    if not schema_data:
        return ""

    # We need to reconstruct a minimal object compatible with _build_schema_panel
    # or just use the raw data.
    class MockTable:
        def __init__(self, cols, measures):
            self.columns = cols
            self.measures = measures

    class MockSchema:
        def __init__(self, tables_dict):
            self.tables = tables_dict

    tables = {}
    for t in schema_data["tables"]:
        tables[t["name"]] = MockTable(t["columns"], t["measures"])

    return _build_schema_panel(MockSchema(tables), search_term or "")
