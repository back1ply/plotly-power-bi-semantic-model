import functools
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TypedDict

import plotly.graph_objects as go

from presentation.theme import COLORS

if False:
    from domain import TemplateLoaderPort


class ModelData(TypedDict):
    tables: list[dict[str, Any]]
    relationships: list[dict[str, Any]]


@dataclass(frozen=True)
class InspectorResult:
    is_open: bool
    content: str


def safe_callback[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    _logger = logging.getLogger("callbacks")

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except Exception:
            _logger.exception("CALLBACK CRASH [%s]", func.__name__)
            raise

    return wrapper


def create_empty_figure(message: str = "No data", height: int = 300) -> go.Figure:
    return go.Figure().update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 20, "color": COLORS["text"]},
            }
        ],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
    )


def load_html_template(loader: "TemplateLoaderPort") -> str:
    return loader.load_html_template("model_diagram.html")


def inject_model_data(html_template: str, model_data: dict) -> str:
    load_script = f"""
    <script>
        window.loadModelData({json.dumps(model_data)});
    </script>
    """
    if "</body>" in html_template:
        return html_template.replace("</body>", load_script + "</body>")
    return html_template + load_script


_AVATAR_COLORS = ["#6366F1", "#14B8A6", "#F59E0B", "#EC4899", "#0EA5E9", "#84CC16"]


def hex_to_rgba(hex_color: str, opacity: float) -> str:
    hex_color = hex_color.lstrip("#")
    hex_length = len(hex_color)
    red_green_blue = tuple(
        int(hex_color[index : index + hex_length // 3], 16)
        for index in range(0, hex_length, hex_length // 3)
    )
    return f"rgba({red_green_blue[0]}, {red_green_blue[1]}, {red_green_blue[2]}, {opacity})"


def avatar_color(name: str) -> str:
    return _AVATAR_COLORS[sum(ord(c) for c in name) % len(_AVATAR_COLORS)]


def initials(name: str) -> str:
    parts = name.split()
    if len(parts) > 1:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()
