"""Query Service.

Handles DAX query generation and formatting.
"""

import logging
from typing import Any

from domain import DaxLoaderPort
from domain import DaxSourcePort
from domain import FragmentCategory
from domain import QueryKey
from domain import QueryNotFoundError

logger = logging.getLogger(__name__)


class QueryService(DaxSourcePort):
    """Handles DAX query generation and formatting."""

    def __init__(self, query_source: DaxLoaderPort) -> None:
        """Initialize with query source."""
        self._source = query_source

    def get_raw_query(self, key: QueryKey) -> str:
        """Get the DAX query text for a given key."""
        try:
            return self._source.get_raw_query(key)
        except (KeyError, QueryNotFoundError) as exc:
            raise QueryNotFoundError(f"Query not found for key: {key}") from exc

    def get_query_template(self, key: str) -> str:
        """Get formattable DAX query string for given key."""
        try:
            return self._source.get_query_template(key)
        except (KeyError, QueryNotFoundError) as exc:
            raise QueryNotFoundError(f"Template not found for key: {key}") from exc

    def get_fragment(self, category: FragmentCategory, key: str) -> str:
        """Get a DAX fragment (e.g., measure or dimension definition)."""
        try:
            return self._source.get_fragment(category, key)
        except (KeyError, QueryNotFoundError) as exc:
            raise QueryNotFoundError(
                f"Fragment not found for {category}/{key}"
            ) from exc

    def get_formatted_query(
        self, key: str, parameters: dict[str, Any] | None = None
    ) -> str:
        """Get a formatted DAX query from a template and parameters."""
        parameters = parameters or {}
        try:
            template = self.get_query_template(key)
            return template.format(**parameters)
        except (KeyError, QueryNotFoundError) as exc:
            raise QueryNotFoundError(
                f"Template or fragments not found for {key} with {parameters}"
            ) from exc

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        """Get the formatted DAX query text for a specific measure and dimension."""
        try:
            measure_dax = self.get_fragment(FragmentCategory.MEASURE, measure_key)
            dimension_dax = self.get_fragment(
                FragmentCategory.DIMENSION, dimension_key
            )
            template = self.get_query_template("summarizecolumns")

            return template.format(
                columns=f"{dimension_dax},", measures=f'"{measure_key}", {measure_dax}'
            )
        except (KeyError, QueryNotFoundError) as exc:
            raise QueryNotFoundError(
                f"Template or fragments not found for {measure_key}/{dimension_key}"
            ) from exc
