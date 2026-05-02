"""Schema Service.

Handles semantic model schema and relationship metadata.
"""

import logging

from domain import DataAnalysisExpressionsSourcePort
from domain import ModelRelationship
from domain import ModelSchema
from domain import QueryClientPort
from domain import QueryError
from domain import QueryKey
from domain import SchemaPort
from domain import TableSchema

logger = logging.getLogger(__name__)


class SchemaService(SchemaPort):
    """Handles semantic model schema and relationship metadata."""

    def __init__(self, query_client: QueryClientPort, query_service: DataAnalysisExpressionsSourcePort) -> None:
        """Initialize with client and query service."""
        self._client = query_client
        self._queries = query_service

    def get_schema(self) -> ModelSchema:
        """Fetch and structure model metadata."""
        try:
            dax_query = self._queries.get_raw_query(QueryKey.MODEL_SCHEMA)
            data_frame = self._client.query(dax_query)
            raw_data = data_frame.to_dicts()

            tables: dict[str, TableSchema] = {}
            for row in raw_data:
                table_name = row["Table"]
                column_name = row["Name"]

                # Defense-in-depth: Filter RowNumber even if metadata flags missed it (XMLA specific)
                if row["Type"] == "Column" and "rownumber" in column_name.lower():
                    continue

                if table_name not in tables:
                    tables[table_name] = TableSchema(name=table_name, columns=[], measures=[])

                if row["Type"] == "Column":
                    tables[table_name].columns.append(column_name)
                else:
                    tables[table_name].measures.append(column_name)

            # Sort names for consistency
            for table in tables.values():
                table.columns.sort()
                table.measures.sort()

            return ModelSchema(tables=dict(sorted(tables.items())))
        except Exception as exception:
            logger.exception("SchemaService.get_schema: failed to fetch schema")
            raise QueryError(f"Failed to fetch model schema: {exception}") from exception

    def get_relationships(self) -> list[ModelRelationship]:
        """Fetch model relationships."""
        try:
            dax_query = self._queries.get_raw_query(QueryKey.MODEL_RELATIONSHIPS)
            data_frame = self._client.query(dax_query)
            raw_relationships = data_frame.to_dicts()
            return [
                ModelRelationship(
                    from_table=relationship.get("FromTable", ""),
                    from_column=relationship.get("FromColumn", ""),
                    to_table=relationship.get("ToTable", ""),
                    to_column=relationship.get("ToColumn", ""),
                    is_active=bool(relationship.get("IsActive", True)),
                    cross_filtering_behavior=str(relationship.get("CrossFilteringBehavior", "OneDirection")),
                    from_cardinality=str(relationship.get("FromCardinality", "")),
                    to_cardinality=str(relationship.get("ToCardinality", "")),
                )
                for relationship in raw_relationships
            ]
        except Exception as exception:
            logger.exception("SchemaService.get_relationships: failed to fetch relationships")
            raise QueryError(f"Failed to fetch model relationships: {exception}") from exception
