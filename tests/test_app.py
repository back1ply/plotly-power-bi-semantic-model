"""Tests for Dash Application Factory."""

import pytest
from dash import Dash
from flask import Flask


def test_app_is_dash_instance():
    from app import app
    assert isinstance(app, Dash)


def test_server_is_flask_instance():
    from app import server
    assert isinstance(server, Flask)


def test_dark_theme_configured():
    from app import app
    layout = app.layout
    assert layout.forceColorScheme == "dark"


def test_app_has_page_container():
    from app import app
    # Search for common Dash page container IDs or markers in the layout string
    layout_str = str(app.layout)
    assert "_pages_content" in layout_str or "page-container" in layout_str


def test_app_uses_pages():
    from app import app
    assert app.config.get("use_pages", True) is True


def test_app_has_inter_font_stylesheet():
    from app import app
    assert any("Inter" in s for s in app.config.external_stylesheets)


def test_sidebar_in_layout():
    from app import app
    assert "Sales Dashboard" in str(app.layout)


def test_connection_banner_in_layout():
    from app import app
    assert "Power BI" in str(app.layout)


def test_dax_inspector_drawer_in_layout():
    from app import app
    assert "dax-inspector-drawer" in str(app.layout)


def test_server_attribute_exists():
    import app
    assert hasattr(app, "server")
