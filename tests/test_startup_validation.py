import pytest
from app import create_app
from domain.exceptions import ConfigurationError
from unittest.mock import patch
import os

def test_app_fails_without_credentials():
    """Verify that create_app raises ConfigurationError when mandatory env vars are missing."""
    # Patch os.getenv to return empty string for required variables
    # We use a side_effect to avoid crashing on integer fields while ensuring IDs are empty
    with patch("os.environ", {}):
        with pytest.raises(ConfigurationError) as excinfo:
            create_app(should_preload=False)
        
        assert "Missing required environment variables" in str(excinfo.value)
        assert "TENANT_ID" in str(excinfo.value)
        assert "CLIENT_ID" in str(excinfo.value)
        assert "CLIENT_SECRET" in str(excinfo.value)

def test_app_starts_with_credentials():
    """Verify that create_app succeeds when mandatory env vars are present."""
    # Mocking environment variables to simulate valid configuration
    mock_env = {
        "TENANT_ID": "test-tenant",
        "CLIENT_ID": "test-client",
        "CLIENT_SECRET": "test-secret",
        "WORKSPACE_ID": "test-workspace",
        "DATASET_ID": "test-dataset",
        "PRELOAD_DATA": "false"
    }
    
    with patch.dict(os.environ, mock_env):
        app = create_app(should_preload=False)
        assert app is not None
        assert app.config["name"] == "app"
