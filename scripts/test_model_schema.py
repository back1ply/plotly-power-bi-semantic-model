"""Test Power BI Semantic Model Schema.

Quick test script to verify that model metadata can be fetched from Power BI.
"""

import logging
from config import AppConfig
from di import DiContainer

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_schema():
    """Execute metadata discovery queries and print summaries."""
    print("--- PBI Schema Inspection ---")

    # 1. Initialize configuration and DiContainer
    config = AppConfig()
    container = DiContainer(config)
    repo = container.repository

    try:
        # 2. Fetch Schema metadata using the repository layer
        print("\nListing Schema metadata...")
        schema = repo.get_schema()

        if not schema or not schema.tables:
            print("FAILED to list tables or schema is empty.")
            return

        print(f"Discovered {len(schema.tables)} tables:")
        for table_name, table in schema.tables.items():
            cols = table.columns
            measures = table.measures
            print(f"  - {table_name}: {len(cols)} columns, {len(measures)} measures")

    except Exception as exc:
        logger.error("Schema inspection failed: %s", exc)
        print(f"Error: {exc}")


if __name__ == "__main__":
    inspect_schema()
