"""Theme and layout constants."""

from config import ThemeConfig

MANTINE_SHADE5_TO_HEX: dict[str, str] = {
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
    primary_hex = MANTINE_SHADE5_TO_HEX.get(primary_color, MANTINE_SHADE5_TO_HEX["blue"])
    rest = [c for c in _DEFAULT_REST if c != primary_hex]
    return [primary_hex, *rest]


_theme = ThemeConfig()

COLORS: dict[str, str] = {
    "primary": MANTINE_SHADE5_TO_HEX.get(_theme.primary_color, MANTINE_SHADE5_TO_HEX["blue"]),
    "secondary": "#4c6ef5",
    "bg": "rgba(0,0,0,0)",
    "plot": "rgba(0,0,0,0)",
    "grid": "#373a40",
    "text": "#909296",
}

CATEGORICAL_PALETTE: list[str] = build_categorical_palette(_theme.primary_color)

# Design tokens ported from claude-pbi-assets reference — adapted for dark mode
DESIGN_TOKENS: dict[str, str] = {
    "accent": "#6366F1",
    "accent_soft": "rgba(99,102,241,0.15)",
    "pos": "#0E9F6E",
    "pos_bg": "rgba(14,159,110,0.12)",
    "neg": "#DC2D4A",
    "neg_bg": "rgba(220,45,74,0.12)",
    "warn": "#B45309",
    "surface": "rgba(255,255,255,0.04)",
    "hairline": "#373a40",
}

# 6-color chart palette matching reference visual palette
CHART_PALETTE: list[str] = [
    "#6366F1",  # indigo
    "#14B8A6",  # teal
    "#F59E0B",  # amber
    "#EC4899",  # pink
    "#0EA5E9",  # sky
    "#84CC16",  # lime
]
