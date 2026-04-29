"""Presentation Formatters.

Contains formatting functions for UI display.
"""

from typing import Any


def format_currency_zero_decimal(value: Any) -> str:
    """Format value as currency with no decimal places."""
    try:
        return f"${float(value):,.0f}"
    except (ValueError, TypeError):
        return str(value)


def format_currency_two_decimals(value: Any) -> str:
    """Format value as currency with two decimal places."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_integer(value: Any) -> str:
    """Format value as a comma-separated integer."""
    try:
        return f"{int(float(value)):,.0f}"
    except (ValueError, TypeError):
        return str(value)
