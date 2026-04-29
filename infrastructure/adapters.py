"""Infrastructure Adapters.

Handles data transformation between infrastructure components and the domain.
"""


def extract_column_name(col: str) -> str:
    """Extract Power BI column from 'Table'[Column] to Column."""
    return col.rsplit("[", 1)[-1].rstrip("]") if "[" in col else col
