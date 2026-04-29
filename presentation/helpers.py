"""Presentation helper functions."""

import json
from pathlib import Path

import plotly.graph_objects as go

from presentation.theme import COLORS


def create_empty_figure(message: str = "No data", height: int = 300) -> go.Figure:
    """Create empty figure with message."""
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


def _load_html_template() -> str:
    """Load the HTML template for the model diagram."""
    template_path = Path(__file__).parent.parent / "assets" / "model_diagram.html"
    return template_path.read_text(encoding="utf-8")


def _inject_model_data(html_template: str, model_data: dict) -> str:
    """Inject model data into the HTML template."""
    load_script = f"""
    <script>
        window.loadModelData({json.dumps(model_data)});
    </script>
    """
    if "</body>" in html_template:
        return html_template.replace("</body>", load_script + "</body>")
    return html_template + load_script
