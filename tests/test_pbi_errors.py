"""Tests for Power BI client error handling edge cases."""

import pytest
from unittest.mock import MagicMock, patch
from domain import AuthenticationError, QueryError, RateLimitError
from infrastructure.auth import MsalTokenProvider
from infrastructure.rate_limiting import SlidingWindowRateLimiter
from infrastructure.power_bi_client import PowerBiClient, PowerBiClientConfiguration


class TestMsalTokenProviderErrors:
    def test_get_token_missing_credentials_raises_error(self):
        provider = MsalTokenProvider("", "", "")
        with pytest.raises(AuthenticationError, match="missing credentials"):
            provider.get_token()

    def test_initialize_failure_raises_error(self):
        # Trigger exception in MSAL constructor
        with patch("infrastructure.auth.ConfidentialClientApplication", side_effect=ValueError("Invalid authority")):
            provider = MsalTokenProvider("t", "c", "s")
            with pytest.raises(AuthenticationError, match="Failed to initialize MSAL"):
                provider.get_token()

    def test_get_token_empty_result_raises_error(self):
        provider = MsalTokenProvider("t", "c", "s")
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {} # Empty dict
        provider._msal_app = mock_app
        
        with pytest.raises(AuthenticationError, match="Could not acquire token"):
            provider.get_token()

    def test_get_token_exception_raises_error(self):
        provider = MsalTokenProvider("t", "c", "s")
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.side_effect = RuntimeError("Socket error")
        provider._msal_app = mock_app
        
        with pytest.raises(AuthenticationError, match="Failed to acquire token"):
            provider.get_token()


class TestRateLimiterErrors:
    def test_rate_limit_exceeded_raises_error(self):
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
        limiter.enforce_rate_limit() # First request OK
        
        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            limiter.enforce_rate_limit()


class TestPowerBiClientErrors:
    @patch("requests.post")
    def test_execute_query_http_failure_raises_query_error(self, mock_post):
        mock_tp = MagicMock()
        mock_tp.get_token.return_value = "token"
        mock_rl = MagicMock()
        config = PowerBiClientConfiguration("w", "d", api_base="https://test.api")
        client = PowerBiClient(mock_tp, mock_rl, config)
        
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"
        mock_post.return_value = mock_resp
        
        with pytest.raises(QueryError, match=r"Power BI query failed \(403\): Forbidden"):
            client._execute_query("EVALUATE Table")

    @patch("requests.post")
    def test_execute_query_empty_results_returns_list(self, mock_post):
        mock_tp = MagicMock()
        mock_tp.get_token.return_value = "token"
        mock_rl = MagicMock()
        config = PowerBiClientConfiguration("w", "d", api_base="https://test.api")
        client = PowerBiClient(mock_tp, mock_rl, config)
        
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"results": []} # No results
        mock_post.return_value = mock_resp

        assert client._execute_query("DAX").is_empty()
    @patch("requests.post")
    def test_execute_query_no_tables_returns_list(self, mock_post):
        mock_tp = MagicMock()
        mock_tp.get_token.return_value = "token"
        mock_rl = MagicMock()
        config = PowerBiClientConfiguration("w", "d", api_base="https://test.api")
        client = PowerBiClient(mock_tp, mock_rl, config)
        
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"results": [{"tables": []}]}
        mock_post.return_value = mock_resp
        
        assert client._execute_query("DAX").is_empty()
