"""Presentation layer.

Contains UI components, charts, callbacks, and constants.
"""

from .constants import DIMENSION_LABELS
from .constants import MEASURE_LABELS
from .helpers import create_empty_figure
from .theme import CATEGORICAL_PALETTE
from .theme import COLORS

__all__ = [
    "CATEGORICAL_PALETTE",
    "COLORS",
    "DIMENSION_LABELS",
    "MEASURE_LABELS",
    "create_empty_figure",
]
