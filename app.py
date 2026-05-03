"""Power BI Sales Dashboard - Main Application Entry Point."""

import logging

from dash import Dash

from config import AppConfig
from config import ThemeConfig
from dependency_injection import DiContainer
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

    # 1.1 Validation (Fail Fast)
    config.validate()

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
            "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-grid.css",
            "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-theme-quartz.css",
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
        </footer>
    </body>
</html>"""

    # 5. Setup Logging Bridge & Shared Resources

    setup_logging_bridge(app)

    # Register in global registry for presentation layer (Eliminates Service Locator)
    from domain import ClassifierPort  # noqa: PLC0415
    from domain import DataAnalysisExpressionsSourcePort  # noqa: PLC0415
    from domain import EmbedPort  # noqa: PLC0415
    from domain import RepositoryPort  # noqa: PLC0415
    from domain import TemplateLoaderPort  # noqa: PLC0415
    from presentation.dependency import registry  # noqa: PLC0415

    registry.register(ClassifierPort, container.classifier)
    registry.register(RepositoryPort, container.repository)
    registry.register(EmbedPort, container.power_bi_embed)
    registry.register(TemplateLoaderPort, container.asset_loader)
    registry.register(DataAnalysisExpressionsSourcePort, container.query_service)

    # Named registration for backward compatibility (Legacy)
    registry.register_named("COLUMN_CLASSIFIER", container.classifier)
    registry.register_named("DASHBOARD_REPOSITORY", container.repository)
    registry.register_named("ASSET_LOADER", container.asset_loader)

    # 6. Register Callbacks (CA-002)
    from presentation.callbacks import register_callbacks  # noqa: PLC0415
    from presentation.routes import register_internal_routes  # noqa: PLC0415

    register_callbacks(
        app,
        data=container.cached_data,
        data_analysis_expressions_query_source=container.query_service,
        client=container.power_bi_client,
        loader=container.asset_loader,
    )
    register_internal_routes(app, pbi_embed=container.power_bi_embed, report_id=config.report_id)

    # 7. Set Layout
    app.layout = create_layout(
        container.power_bi_client.has_credentials,
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
    app.run(
        debug=config.debug,
        host="127.0.0.1",
        port=8050,
        dev_tools_ui=True,
        dev_tools_serve_dev_bundles=True,
    )
else:
    # Singleton instance for Gunicorn/Prod
    # side-effect-free import (preload_data defaults to False)
    app = create_app()
    server = app.server
