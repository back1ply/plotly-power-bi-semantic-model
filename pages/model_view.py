"""Model View Diagram Page.

Displays the Power BI semantic model as a relationship diagram.
Styled to match Power BI's Model View appearance.
"""

import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from domain import ClassifierPort
from domain import ColumnType
from domain import ModelRelationship
from domain import ModelSchema
from domain import QueryError
from domain import SchemaPort
from domain import TemplateLoaderPort
from presentation.dependency import get_repository
from presentation.dependency import get_service
from presentation.helpers import inject_model_data
from presentation.helpers import load_html_template

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


def _build_model_data(
    schema: ModelSchema, relationships: list[ModelRelationship], classifier: ClassifierPort
) -> dict:
    """Build model data structure for the JavaScript visualization."""
    tables = []

    for table_name, table in schema.tables.items():
        raw_columns = table.columns
        measures = table.measures

        columns = []
        for column in raw_columns:
            column_type = classifier.detect_type(column, table_name)
            if column_type != ColumnType.HIDDEN:
                columns.append({"name": column, "type": column_type.value})

        for measure in measures:
            columns.append({"name": measure, "type": ColumnType.MEASURE.value})

        # Final list of visible items
        visible_columns = columns[:MAX_COLUMNS_DISPLAY]
        extra_count = len(columns) - MAX_COLUMNS_DISPLAY

        tables.append(
            {
                "id": table_name,
                "name": table_name,
                "columns": visible_columns,
                "extraColumns": max(0, extra_count),
            }
        )

    relationships_list = []
    for relationship in relationships:
        from_cardinality = relationship.from_cardinality
        to_cardinality = relationship.to_cardinality

        source_label = (
            "1"
            if from_cardinality and "One" in from_cardinality
            else ("*" if from_cardinality and "Many" in from_cardinality else "?")
        )
        target_label = (
            "1"
            if to_cardinality and "One" in to_cardinality
            else ("*" if to_cardinality and "Many" in to_cardinality else "?")
        )

        relationships_list.append(
            {
                "from": relationship.from_table,
                "fromColumn": relationship.from_column,
                "to": relationship.to_table,
                "toColumn": relationship.to_column,
                "cardinality": f"{source_label}:{target_label}",
                "crossFilteringBehavior": relationship.cross_filtering_behavior,
                "active": relationship.is_active,
            }
        )

    return {"tables": tables, "relationships": relationships_list}


def layout() -> dmc.Stack | dmc.Alert:
    """Create the model view layout."""
    repository = get_repository(SchemaPort)
    classifier = get_service(ClassifierPort)
    loader = get_service(TemplateLoaderPort)
    return serve_layout(repository, classifier, loader)


def serve_layout(
    repository: SchemaPort, classifier: ClassifierPort, loader: TemplateLoaderPort
) -> dmc.Stack | dmc.Alert:
    """Logic to build the layout, separated for testability. (CA-003)"""
    try:
        schema = repository.get_schema()
        relationships = repository.get_relationships()
    except QueryError as exception:
        return dmc.Alert(
            f"Failed to load model diagram: {exception}",
            title="Diagram Fetch Error",
            color="red",
            variant="filled",
            icon=DashIconify(icon="tabler:alert-circle"),
            mt="xl",
        )

    model_data = _build_model_data(schema, relationships, classifier)
    html_template = load_html_template(loader)
    html_with_data = inject_model_data(html_template, model_data)

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
