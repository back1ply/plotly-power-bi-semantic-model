"""Domain Services.

Contains domain-level business logic and services.
"""

from domain import ColumnType


class ColumnClassifier:
    """Classifies model columns based on naming patterns and table context."""

    _RULES = {
        ColumnType.HIDDEN: ["rownumber", "internal", "objectid"],
        ColumnType.KEY: ["key", "id", "pk", "surrogate"],
        ColumnType.DATE: ["date", "year", "month", "quarter", "day", "time", "fiscal"],
    }

    _TABLE_SPECIFIC_RULES = {
        "sales": {
            ColumnType.MEASURE: [
                "amount",
                "cost",
                "quantity",
                "sales",
                "revenue",
                "profit",
                "total",
            ]
        }
    }

    @classmethod
    def detect_type(cls, col_name: str, table_name: str) -> ColumnType:
        """Detect column type using a rule-based approach. (OO-005)"""
        col_lower = col_name.lower()
        table_lower = table_name.lower()

        # 1. Check general rules
        for col_type, patterns in cls._RULES.items():
            if any(p in col_lower for p in patterns):
                return col_type

        # 2. Check table-specific rules
        if table_lower in cls._TABLE_SPECIFIC_RULES:
            for col_type, patterns in cls._TABLE_SPECIFIC_RULES[table_lower].items():
                if any(p in col_lower for p in patterns):
                    return col_type

        return ColumnType.REGULAR
