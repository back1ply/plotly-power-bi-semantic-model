"""Resilience and Chaos Tests for Power BI Embed Service."""

import pytest
from unittest.mock import MagicMock, patch
import requests
from infrastructure.power_bi_embed import PowerBiEmbedService
from infrastructure.power_bi_client import PowerBiClientConfiguration
from domain import QueryError, TokenProviderPort

@pytest.fixture
def mock_embed_deps():
    token_provider = MagicMock(spec=TokenProviderPort)
    token_provider.get_token.return_value = "fake-token"
    
    config = PowerBiClientConfiguration(
        workspace_id="w",
        dataset_id="d",
        api_base="https://api.powerbi.com",
        request_timeout=1
    )
    
    return token_provider, config

class TestResilienceEmbed:
    def test_fetch_metadata_failure_raises_query_error(self, mock_embed_deps):
        """Verify that failure to fetch report metadata raises QueryError."""
        tp, cfg = mock_embed_deps
        service = PowerBiEmbedService(tp, cfg)
        
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        mock_resp.text = "Report not found"
        
        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(QueryError, match="Failed to fetch report metadata \(404\)"):
                service.get_embed_config("r-id")

    def test_token_generation_failure_raises_query_error(self, mock_embed_deps):
        """Verify that failure to generate embed token raises QueryError."""
        tp, cfg = mock_embed_deps
        service = PowerBiEmbedService(tp, cfg)
        
        # 1. Success on GET metadata
        mock_get_resp = MagicMock()
        mock_get_resp.ok = True
        mock_get_resp.json.return_value = {"embedUrl": "https://embed.url", "datasetId": "d-id"}
        
        # 2. Failure on POST token
        mock_post_resp = MagicMock()
        mock_post_resp.ok = False
        mock_post_resp.status_code = 400
        mock_post_resp.text = "Bad Request"
        
        with patch("requests.get", return_value=mock_get_resp):
            with patch("requests.post", return_value=mock_post_resp):
                with pytest.raises(QueryError, match="Failed to generate embed token \(400\)"):
                    service.get_embed_config("r-id")

    def test_network_failure_generic_wrapping(self, mock_embed_deps):
        """Verify that generic network exceptions are wrapped."""
        tp, cfg = mock_embed_deps
        service = PowerBiEmbedService(tp, cfg)
        
        with patch("requests.get", side_effect=requests.ConnectionError("DNS failure")):
            with pytest.raises(QueryError, match="Power BI embedding failure"):
                service.get_embed_config("r-id")

    def test_get_embed_config_success(self, mock_embed_deps):
        """Verify the happy path for the embed service."""
        tp, cfg = mock_embed_deps
        service = PowerBiEmbedService(tp, cfg)
        
        mock_get_resp = MagicMock()
        mock_get_resp.ok = True
        mock_get_resp.json.return_value = {"embedUrl": "https://embed.url", "datasetId": "d-id"}
        
        mock_post_resp = MagicMock()
        mock_post_resp.ok = True
        mock_post_resp.json.return_value = {"token": "embed-token-123"}
        
        with patch("requests.get", return_value=mock_get_resp):
            with patch("requests.post", return_value=mock_post_resp):
                result = service.get_embed_config("r-id")
                assert result.report_id == "r-id"
                assert result.embed_url == "https://embed.url"
                assert result.access_token == "embed-token-123"
