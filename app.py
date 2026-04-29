"""Power BI Sales Dashboard - Main Application Entry Point."""

import logging

from dash import Dash
from flask import abort
from flask import jsonify

from config import AppConfig
from config import ThemeConfig
from di import DiContainer
from domain import LoadResult
from layout import create_layout
from presentation.logging_bridge import setup_logging_bridge

logger = logging.getLogger(__name__)


def _load_startup_data(container: DiContainer, config: AppConfig) -> LoadResult:
    """Populate cache at startup with fail-safe logic."""
    logger.info("Initializing Power BI data cache...")
    try:
        return container.data_loader.populate_cache(
            max_attempts=config.max_retries,
            base_delay=config.retry_delay,
        )
    except Exception as exc:
        logger.error("Initial cache population failed: %s", exc)
        return LoadResult(
            success=False,
            loaded_keys=[],
            errors={"startup": str(exc)},
        )


def create_app(container: DiContainer | None = None, should_preload: bool | None = None) -> Dash:
    """Application factory for the Power BI Sales Dashboard.

    Initializes configuration, PBI client, and cache before returning
    the Dash application instance.
    """
    # 1. Configuration
    config = AppConfig()

    # 2. Initialize Dependency Container (Composition Root)
    if container is None:
        container = DiContainer(config)

    # 3. Populate cache (Optional for testing)
    load_result = LoadResult(success=True, loaded_keys=[], errors={})

    # Use parameter override or config default
    preload_enabled = should_preload if should_preload is not None else config.preload_data

    if preload_enabled:
        load_result = _load_startup_data(container, config)

    # 4. Initialize Dash
    app = Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            "https://unpkg.com/@mantine/core@7/styles.css",
            "https://unpkg.com/@mantine/dates@7/styles.css",
        ],
    )

    # Inject scripts at the very end of body to avoid RequireJS/AMD conflicts with Dash bundles
    app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
            <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs/loader.js"></script>
        </footer>
    </body>
</html>"""

    # 5. Setup Logging Bridge & Shared Resources

    setup_logging_bridge(app)
    app.server.config["PBI_CLIENT"] = container.pbi_client
    app.server.config["PBI_EMBED"] = container.pbi_embed
    app.server.config["DASHBOARD_REPOSITORY"] = container.repository
    app.server.config["REPORT_ID"] = config.report_id

    # 6. Register Callbacks (CA-002)
    from presentation.callbacks import register_callbacks  # noqa: PLC0415

    register_callbacks(app, container.repository)

    # 7. Define Health Check
    logger.info("Setting up internal routes...")
    @app.server.route("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    # 7b. Embed Config Endpoint (app-owns-data, service principal)
    @app.server.route("/api/embed-config")
    def embed_config():
        from domain import EmbedPort  # noqa: PLC0415

        pbi: EmbedPort = app.server.config["PBI_EMBED"]
        report_id: str = app.server.config.get("REPORT_ID", "")
        if not report_id:
            abort(503, description="REPORT_ID not configured")
        try:
            cfg = pbi.get_embed_config(report_id)
            return jsonify(cfg)
        except Exception as exc:
            logger.error("embed_config failed: %s", exc)
            abort(502, description=str(exc))


    # 8. Set Layout
    app.layout = create_layout(
        container.pbi_client.has_credentials,
        load_result.errors,
        theme=ThemeConfig(),
    )

    logger.info("App initialization complete.")
    return app


if __name__ == "__main__":
    # Explicitly preload data in development
    config = AppConfig()
    container = DiContainer(config)
    
    # Preload cache at startup (non-blocking for server startup in local dev)
    try:
        _load_startup_data(container, config)
    except Exception as exc:
        logger.error("Non-fatal preloading failure: %s", exc)

    app = create_app(container=container, should_preload=False)
    app.run(debug=config.debug, host="127.0.0.1", port=8050, dev_tools_ui=config.debug)
else:
    # Singleton instance for Gunicorn/Prod
    # side-effect-free import (preload_data defaults to False)
    app = create_app()
    server = app.server
