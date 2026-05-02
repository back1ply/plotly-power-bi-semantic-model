"""Infrastructure utilities.

Contains generic utilities used in the infrastructure layer.
"""

import logging
from typing import Any

from .adapters import extract_column_name

logger = logging.getLogger(__name__)


class PowerBiResponseParser:
    """Handles parsing and transformation of Power BI API responses. (OO-003, API-004)"""

    @staticmethod
    def parse_execute_queries_response(data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract records from a Power BI executeQueries response.

        Args:
            data: The JSON response dictionary from Power BI API.

        Returns:
            A list of records as dictionaries with cleaned column names.

        Raises:
            ValueError: If the response contains a Power BI execution error.
        """
        results = data.get("results", [])
        if not results:
            return []

        # Check for error in the first result (Power BI often returns 200 with error in JSON)
        if "error" in results[0]:
            error_msg = results[0]["error"].get("message", "Unknown Power BI execution error")
            logger.error("Power BI execution error in results: %s", error_msg)
            raise ValueError(error_msg)

        tables = results[0].get("tables", [])
        if not tables:
            return []

        rows = tables[0].get("rows", [])
        if not rows:
            return []

        return [
            {extract_column_name(column_key): cell_value for column_key, cell_value in row.items()}
            for row in rows
        ]
