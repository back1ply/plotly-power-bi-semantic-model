"""Fetch Power BI Semantic Model Schema.

Standalone script to discover tables, columns, and measures using the
Power BI repository layer and save them to a JSON file.
"""

import json
import logging
from pathlib import Path

from config import AppConfig
from di import DiContainer

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"


def discover_full_schema():
    """Fetch model schema using the repository layer."""
    # 1. Initialize configuration and DiContainer
    config = AppConfig()
    container = DiContainer(config)
    repo = container.repository

    print("Fetching full model metadata from repository...")

    try:
        # Uses the new fetch_schema() which abstracts the INFO functions
        schema = repo.get_schema()

        table_count = len(schema.tables)

        col_count = sum(len(table.columns) for table in schema.tables.values())
        measure_count = sum(len(table.measures) for table in schema.tables.values())

        print(
            f"Found {table_count} tables, {col_count} columns, and {measure_count} measures."
        )

        # 2. Save structured schema
        from dataclasses import asdict  # noqa: PLC0415

        OUTPUT_DIR.mkdir(exist_ok=True)
        output_path = OUTPUT_DIR / "model_schema.json"
        with output_path.open("w") as f:
            json.dump(asdict(schema), f, indent=2)

        print(f"Schema saved to {output_path}")

    except Exception as exc:
        logger.error("Failed to discover schema: %s", exc)
        print(f"Error: {exc}")


if __name__ == "__main__":
    discover_full_schema()
