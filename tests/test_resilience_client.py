"""Resilience and Chaos Tests for Power BI Client."""

import pytest
from unittest.mock import MagicMock, patch
import requests
from infrastructure.power_bi_client import PowerBiClient, PowerBiClientConfiguration
from domain import QueryError, TokenProviderPort, RateLimiterPort

@pytest.fixture
def mock_deps():
    token_provider = MagicMock(spec=TokenProviderPort)
    token_provider.get_token.return_value = "fake-token"
    token_provider.has_credentials = True
    
    rate_limiter = MagicMock(spec=RateLimiterPort)
    
    config = PowerBiClientConfiguration(
        workspace_id="w",
        dataset_id="d",
        api_base="https://api.powerbi.com",
        request_timeout=1
    )
    
    return token_provider, rate_limiter, config

class TestResilienceClient:
    def test_http_401_error_wraps_in_query_error(self, mock_deps):
        """Verify that 401 Unauthorized is caught and raised as QueryError."""
        tp, rl, cfg = mock_deps
        client = PowerBiClient(tp, rl, cfg)
        
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match="failed \(401\)"):
                client.query("EVALUATE 'Table'")

    def test_http_429_error_wraps_in_query_error(self, mock_deps):
        """Verify that 429 Too Many Requests is caught and raised as QueryError."""
        tp, rl, cfg = mock_deps
        client = PowerBiClient(tp, rl, cfg)
        
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match="failed \(429\)"):
                client.query("EVALUATE 'Table'")

    def test_network_timeout_wraps_in_query_error(self, mock_deps):
        """Verify that requests.exceptions.Timeout is caught and raised as QueryError."""
        tp, rl, cfg = mock_deps
        client = PowerBiClient(tp, rl, cfg)
        
        with patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
            with pytest.raises(QueryError, match="network or connection failure"):
                client.query("EVALUATE 'Table'")

    def test_malformed_json_response_wraps_in_query_error(self, mock_deps):
        """Verify that invalid JSON from API is raised as QueryError."""
        tp, rl, cfg = mock_deps
        client = PowerBiClient(tp, rl, cfg)
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Expecting value: line 1 column 1")
        
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match="response parsing failure"):
                client.query("EVALUATE 'Table'")

    def test_missing_results_returns_empty_dataframe(self, mock_deps):
        """Verify that empty results dictionary returns empty Polars DataFrame."""
        tp, rl, cfg = mock_deps
        client = PowerBiClient(tp, rl, cfg)
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"results": []}
        
        with patch("requests.post", return_value=mock_response):
            df = client.query("EVALUATE 'Table'")
            assert df.is_empty()

    def test_missing_tables_returns_empty_dataframe(self, mock_deps):
        """Verify that results with no tables returns empty Polars DataFrame."""
        tp, rl, cfg = mock_deps
        client = PowerBiClient(tp, rl, cfg)
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"results": [{"tables": []}]}
        
        with patch("requests.post", return_value=mock_response):
            df = client.query("EVALUATE 'Table'")
            assert df.is_empty()
