"""Integration tests for the Dash/Flask API contract.

These tests serve as 'Gates' to ensure that the server configuration 
provided in app.py matches the keys expected by presentation/routes.py.
"""

import pytest
from unittest.mock import MagicMock
from app import create_app
from domain import EmbedConfig

@pytest.fixture
def mock_app():
    """Create a test app with all required infrastructure mocked."""
    mock_container = MagicMock()
    
    # Mock Embed Service
    mock_pbi_embed = MagicMock()
    mock_pbi_embed.get_embed_config.return_value = EmbedConfig(
        report_id="gate-test-id",
        embed_url="https://gate.test/embed",
        access_token="gate-token"
    )
    mock_container.power_bi_embed = mock_pbi_embed
    
    # Mock Client
    mock_container.power_bi_client.has_credentials = True
    
    return create_app(container=mock_container, should_preload=False)

def test_gate_health_endpoint(mock_app):
    """GATE: Verify health check route is registered and working."""
    client = mock_app.server.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_gate_embed_config_contract(mock_app):
    """GATE: Verify the contract between app.py config and routes.py.
    
    This catches mismatches like 'POWER_BI_EMBED' vs 'PBI_EMBED'.
    """
    client = mock_app.server.test_client()
    
    # This call will fail with 503 if PBI_EMBED or REPORT_ID are missing or misnamed
    response = client.get("/api/embed-config")
    
    assert response.status_code == 200, (
        f"API Contract Violation: /api/embed-config returned {response.status_code}. "
        "Check if app.py server config keys match presentation/routes.py requirements."
    )
    
    data = response.get_json()
    assert "reportId" in data
    assert "embedUrl" in data
    assert "accessToken" in data

def test_gate_static_assets(mock_app):
    """GATE: Verify that critical static assets are served."""
    client = mock_app.server.test_client()
    assets = [
        "/assets/style.css",
        "/assets/dax-ace-mode.js",
        "/assets/dax-ace-completions.js",
        "/assets/embed_init.js"
    ]
    
    for asset in assets:
        response = client.get(asset)
        assert response.status_code == 200, f"Static asset {asset} is missing or not served."
        assert len(response.data) > 0, f"Static asset {asset} is empty."
