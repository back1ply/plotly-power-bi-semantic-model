"""Tests for Registry and Enum consistency.

Ensures that the QueryKey enum matches the keys defined in dax.json.
Provides an automated gate against attribute errors during refactoring.
"""

import json
from pathlib import Path
from domain import QueryKey


def test_query_key_enum_matches_dax_json():
    """Verify that every key in dax.json 'startup' has a corresponding QueryKey member."""
    dax_path = Path(__file__).parent.parent / "queries" / "dax.json"
    with open(dax_path, "r", encoding="utf-8") as f:
        dax_config = json.load(f)

    startup_keys = set(dax_config.get("startup", {}).keys())
    enum_values = {member.value for member in QueryKey}

    # 1. Check for missing values in Enum (DAX key exists but Enum doesn't map to it)
    missing_in_enum = startup_keys - enum_values
    assert not missing_in_enum, f"Keys in dax.json missing from QueryKey enum: {missing_in_enum}"

    # 2. Check for stale enum members (Enum maps to a key that doesn't exist in DAX)
    # Note: We allow this if it's expected, but usually it should be 1:1
    stale_in_enum = enum_values - startup_keys
    assert not stale_in_enum, f"QueryKey members mapping to non-existent DAX keys: {stale_in_enum}"


def test_required_query_key_attributes_exist():
    """Verify that required attributes used by the application are defined in the enum.
    
    This catches cases where an enum member exists with a value, but the attribute 
    name itself was renamed (e.g., TREND_DATA -> SALES_TREND_DATA).
    """
    required_attributes = [
        "TREND_DATA",
        "CATEGORY_DATA",
        "TERRITORY_DATA",
        "TOP_N_DATA",
        "KEY_PERFORMANCE_INDICATOR_TOTALS",
        "MODEL_SCHEMA",
        "MODEL_RELATIONSHIPS",
    ]
    
    for attr in required_attributes:
        assert hasattr(QueryKey, attr), f"QueryKey is missing required attribute: {attr}"
