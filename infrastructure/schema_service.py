"""Schema Service.

Handles semantic model schema and relationship metadata.
"""

import logging

from domain import DaxSourcePort
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

    def __init__(
        self, query_client: QueryClientPort, query_service: DaxSourcePort
    ) -> None:
        """Initialize with client and query service."""
        self._client = query_client
        self._queries = query_service

    def get_schema(self) -> ModelSchema:
        """Fetch and structure model metadata."""
        try:
            dax = self._queries.get_raw_query(QueryKey.MODEL_SCHEMA)
            raw_data = self._client.query(dax)

            tables: dict[str, TableSchema] = {}
            for row in raw_data:
                table_name = row["Table"]
                col_name = row["Name"]

                # Defense-in-depth: Filter RowNumber even if metadata flags missed it (XMLA specific)
                if row["Type"] == "Column" and "rownumber" in col_name.lower():
                    continue

                if table_name not in tables:
                    tables[table_name] = TableSchema(
                        name=table_name, columns=[], measures=[]
                    )

                if row["Type"] == "Column":
                    tables[table_name].columns.append(col_name)
                else:
                    tables[table_name].measures.append(col_name)

            # Sort names for consistency
            for table in tables.values():
                table.columns.sort()
                table.measures.sort()

            return ModelSchema(tables=dict(sorted(tables.items())))
        except Exception as exc:
            logger.exception("SchemaService.get_schema: failed to fetch schema")
            raise QueryError(f"Failed to fetch model schema: {exc}") from exc

    def get_relationships(self) -> list[ModelRelationship]:
        """Fetch model relationships."""
        try:
            dax = self._queries.get_raw_query(QueryKey.MODEL_RELATIONSHIPS)
            raw_rels = self._client.query(dax)
            return [
                ModelRelationship(
                    from_table=rel.get("FromTable", ""),
                    from_column=rel.get("FromColumn", ""),
                    to_table=rel.get("ToTable", ""),
                    to_column=rel.get("ToColumn", ""),
                    is_active=bool(rel.get("IsActive", True)),
                    cross_filtering_behavior=str(
                        rel.get("CrossFilteringBehavior", "OneDirection")
                    ),
                    from_cardinality=str(rel.get("FromCardinality", "")),
                    to_cardinality=str(rel.get("ToCardinality", "")),
                )
                for rel in raw_rels
            ]
        except Exception as exc:
            logger.exception(
                "SchemaService.get_relationships: failed to fetch relationships"
            )
            raise QueryError(f"Failed to fetch model relationships: {exc}") from exc
