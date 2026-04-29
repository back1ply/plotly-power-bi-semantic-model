"""Theme and layout constants."""

from config import ThemeConfig

_MANTINE_SHADE5: dict[str, str] = {
    "blue": "#228be6",
    "violet": "#7950f2",
    "teal": "#20c997",
    "green": "#40c057",
    "yellow": "#fab005",
    "orange": "#fd7e14",
    "red": "#fa5252",
    "pink": "#e64980",
    "cyan": "#15aabf",
    "grape": "#be4bdb",
    "indigo": "#4c6ef5",
    "lime": "#94d82d",
}

_DEFAULT_REST: list[str] = [
    "#40c057",
    "#fab005",
    "#fd7e14",
    "#fa5252",
    "#be4bdb",
    "#15aabf",
]


def build_categorical_palette(primary_color: str) -> list[str]:
    """Build chart color palette with PRIMARY_COLOR as first slot, no duplicates."""
    primary_hex = _MANTINE_SHADE5.get(primary_color, _MANTINE_SHADE5["blue"])
    rest = [c for c in _DEFAULT_REST if c != primary_hex]
    return [primary_hex, *rest]


_theme = ThemeConfig()

COLORS: dict[str, str] = {
    "primary": _MANTINE_SHADE5.get(_theme.primary_color, _MANTINE_SHADE5["blue"]),
    "secondary": "#4c6ef5",
    "bg": "rgba(0,0,0,0)",
    "plot": "rgba(0,0,0,0)",
    "grid": "#373a40",
    "text": "#909296",
}

CATEGORICAL_PALETTE: list[str] = build_categorical_palette(_theme.primary_color)
