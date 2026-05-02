from enum import StrEnum


class Orientation(StrEnum):
    VERTICAL = "v"
    HORIZONTAL = "h"


class SortOrder(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"
    NONE = "none"
