"""Resilience and Chaos Tests for Authentication."""

import pytest
from unittest.mock import MagicMock, patch
from infrastructure.auth import MsalTokenProvider
from domain import AuthenticationError

class TestResilienceAuth:
    def test_missing_credentials_throws_error(self):
        """Verify that provider throws AuthenticationError when credentials are missing."""
        provider = MsalTokenProvider(tenant_id="", client_id="", client_secret="")
        with pytest.raises(AuthenticationError, match="missing credentials"):
            provider.get_token()

    def test_msal_initialization_failure(self):
        """Verify that MSAL init errors are wrapped in AuthenticationError."""
        provider = MsalTokenProvider("t", "c", "s")
        with patch("infrastructure.auth.ConfidentialClientApplication", side_effect=Exception("Network down")):
            with pytest.raises(AuthenticationError, match="Failed to initialize MSAL"):
                provider.get_token()

    def test_token_acquisition_returns_no_token(self):
        """Verify that MSAL response with error/no-token throws AuthenticationError."""
        provider = MsalTokenProvider("t", "c", "s")
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Client secret is expired"
        }
        
        with patch("infrastructure.auth.ConfidentialClientApplication", return_value=mock_app):
            with pytest.raises(AuthenticationError, match="Client secret is expired"):
                provider.get_token()

    def test_token_acquisition_generic_exception(self):
        """Verify that generic exceptions during acquisition are wrapped."""
        provider = MsalTokenProvider("t", "c", "s")
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.side_effect = RuntimeError("SSL Fail")
        
        with patch("infrastructure.auth.ConfidentialClientApplication", return_value=mock_app):
            with pytest.raises(AuthenticationError, match="Failed to acquire token"):
                provider.get_token()

    def test_lazy_initialization_happens_only_once(self):
        """Verify that _initialize is only called on the first get_token call."""
        provider = MsalTokenProvider("t", "c", "s")
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {"access_token": "token123"}
        
        with patch("infrastructure.auth.ConfidentialClientApplication", return_value=mock_app) as mock_init:
            provider.get_token()
            provider.get_token()
            assert mock_init.call_count == 1
