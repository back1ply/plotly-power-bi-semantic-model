"""Model View Diagram Page.

Displays the Power BI semantic model as a relationship diagram.
Styled to match Power BI's Model View appearance.
"""

import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from domain import ColumnType
from domain import ModelSchema
from domain import QueryError
from domain import SchemaPort
from domain.services import ColumnClassifier
from presentation.dependency import get_repository
from presentation.helpers import _inject_model_data
from presentation.helpers import _load_html_template

MAX_COLUMNS_DISPLAY = 12

# Validation layout fragment for app.py (OO-002)
VALIDATION_LAYOUT = html.Div(
    [
        html.Iframe(id="model-diagram-frame"),
    ]
)


# Register page at module level
dash.register_page(
    __name__,
    path="/model",
    name="Model Diagram",
    order=3,
)


def _build_model_data(schema: ModelSchema, relationships: list) -> dict:
    """Build model data structure for the JavaScript visualization."""
    tables = []

    for table_name, table in schema.tables.items():
        raw_cols = table.columns
        measures = table.measures

        columns = []
        for col in raw_cols:
            col_type = ColumnClassifier.detect_type(col, table_name)
            if col_type != ColumnType.HIDDEN:
                columns.append({"name": col, "type": col_type.value})

        for measure in measures:
            columns.append({"name": measure, "type": ColumnType.MEASURE.value})

        # Final list of visible items
        visible_cols = columns[:MAX_COLUMNS_DISPLAY]
        extra_count = len(columns) - MAX_COLUMNS_DISPLAY

        tables.append(
            {
                "id": table_name,
                "name": table_name,
                "columns": visible_cols,
                "extraColumns": max(0, extra_count),
            }
        )

    rels = []
    for rel in relationships:
        from_card = rel.from_cardinality
        to_card = rel.to_cardinality

        s_label = (
            "1"
            if from_card and "One" in from_card
            else ("*" if from_card and "Many" in from_card else "?")
        )
        t_label = (
            "1" if to_card and "One" in to_card else ("*" if to_card and "Many" in to_card else "?")
        )

        rels.append(
            {
                "from": rel.from_table,
                "fromColumn": rel.from_column,
                "to": rel.to_table,
                "toColumn": rel.to_column,
                "cardinality": f"{s_label}:{t_label}",
                "crossFilteringBehavior": rel.cross_filtering_behavior,
                "active": rel.is_active,
            }
        )

    return {"tables": tables, "relationships": rels}


def layout() -> dmc.Stack | dmc.Alert:
    """Create the model view layout."""
    repo = get_repository(SchemaPort)
    return serve_layout(repo)


def serve_layout(repo: SchemaPort) -> dmc.Stack | dmc.Alert:
    """Logic to build the layout, separated for testability. (CA-003)"""
    try:
        schema = repo.get_schema()
        relationships = repo.get_relationships()
    except QueryError as exc:
        return dmc.Alert(
            f"Failed to load model diagram: {exc}",
            title="Diagram Fetch Error",
            color="red",
            variant="filled",
            icon=DashIconify(icon="tabler:alert-circle"),
            mt="xl",
        )

    model_data = _build_model_data(schema, relationships)
    html_template = _load_html_template()
    html_with_data = _inject_model_data(html_template, model_data)

    return dmc.Stack(
        gap="md",
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Stack(
                        gap=0,
                        children=[
                            dmc.Title("Model Diagram", order=3, fw=700),
                            dmc.Text(
                                "Star schema visualization matching Power BI Model View style.",
                                size="sm",
                                c="dimmed",
                            ),
                        ],
                    ),
                ],
            ),
            dmc.Paper(
                withBorder=True,
                radius="md",
                shadow="sm",
                style={"height": "78vh", "overflow": "hidden", "background": "#F3F2F1"},
                children=[
                    html.Iframe(
                        id="model-diagram-frame",
                        srcDoc=html_with_data,
                        style={
                            "width": "100%",
                            "height": "100%",
                            "border": "none",
                        },
                    )
                ],
            ),
            dmc.Text(
                "Tip: Drag tables to arrange. Scroll to zoom. Right-click for options.",
                size="xs",
                c="dimmed",
                mt="xs",
            ),
        ],
    )
