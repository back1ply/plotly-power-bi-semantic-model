"""Internal API routes for the Dash application."""

import logging
from dataclasses import asdict

from dash import Dash
from flask import jsonify

from domain import EmbedPort

logger = logging.getLogger(__name__)


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def serialize_camel_case(obj: object) -> dict:
    """Serialize a dataclass to a dictionary with camelCase keys."""
    return {to_camel_case(k): v for k, v in asdict(obj).items()}


def register_internal_routes(app: Dash, pbi_embed: EmbedPort, report_id: str) -> None:
    """Register internal Flask routes on the Dash server."""

    @app.server.route("/api/health")
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "ok"})

    @app.server.route("/api/embed-config")
    def embed_config():
        """Embed Config Endpoint (app-owns-data, service principal)."""
        if not pbi_embed:
            return jsonify({"error": "Embed service not configured"}), 503
        if not report_id:
            return jsonify({"error": "REPORT_ID not configured"}), 503

        try:
            cfg = pbi_embed.get_embed_config(report_id)
            return jsonify(serialize_camel_case(cfg))
        except Exception as exc:
            logger.error("embed_config failed: %s", exc)
            return jsonify({"error": str(exc)}), 502
