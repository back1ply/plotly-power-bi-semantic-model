"""Domain Services.

Contains domain-level business logic and services.
"""

from typing import ClassVar

from domain import ClassifierPort
from domain import ColumnType


class ColumnClassifier(ClassifierPort):
    """Classifies model columns based on naming patterns and table context."""

    DEFAULT_RULES: ClassVar[dict[ColumnType, list[str]]] = {
        ColumnType.HIDDEN: ["rownumber", "internal", "objectid"],
        ColumnType.KEY: ["key", "id", "pk", "surrogate"],
        ColumnType.DATE: ["date", "year", "month", "quarter", "day", "time", "fiscal"],
    }

    DEFAULT_TABLE_RULES: ClassVar[dict[str, dict[ColumnType, list[str]]]] = {
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

    def __init__(
        self,
        rules: dict[ColumnType, list[str]] | None = None,
        table_rules: dict[str, dict[ColumnType, list[str]]] | None = None,
        use_defaults: bool = True,
    ) -> None:
        """Initialize classifier with optional rules. (OO-005)

        Args:
            rules: General classification rules.
            table_rules: Table-specific classification rules.
            use_defaults: Whether to include hardcoded default rules.
        """
        self._rules: dict[ColumnType, list[str]] = {}
        self._table_specific_rules: dict[str, dict[ColumnType, list[str]]] = {}

        if use_defaults:
            self._rules.update(self.DEFAULT_RULES)
            self._table_specific_rules.update(self.DEFAULT_TABLE_RULES)

        if rules:
            for col_type, patterns in rules.items():
                self.register_rule(col_type, patterns)

        if table_rules:
            for table_name, t_rules in table_rules.items():
                for col_type, patterns in t_rules.items():
                    self.register_table_rule(table_name, col_type, patterns)

    def register_rule(self, col_type: ColumnType, patterns: list[str]) -> None:
        """Register new general classification rules. (OO-005)"""
        if col_type not in self._rules:
            self._rules[col_type] = []
        self._rules[col_type].extend([p.lower() for p in patterns])

    def register_table_rule(
        self, table_name: str, col_type: ColumnType, patterns: list[str]
    ) -> None:
        """Register new table-specific classification rules. (OO-005)"""
        table_lower = table_name.lower()
        if table_lower not in self._table_specific_rules:
            self._table_specific_rules[table_lower] = {}
        if col_type not in self._table_specific_rules[table_lower]:
            self._table_specific_rules[table_lower][col_type] = []
        self._table_specific_rules[table_lower][col_type].extend([p.lower() for p in patterns])

    def detect_type(self, col_name: str, table_name: str) -> ColumnType:
        """Detect column type using a rule-based approach. (OO-005)"""
        col_lower = col_name.lower()
        table_lower = table_name.lower()

        # 1. Check general rules
        for col_type, patterns in self._rules.items():
            if any(p in col_lower for p in patterns):
                return col_type

        # 2. Check table-specific rules
        if table_lower in self._table_specific_rules:
            for col_type, patterns in self._table_specific_rules[table_lower].items():
                if any(p in col_lower for p in patterns):
                    return col_type

        return ColumnType.REGULAR
