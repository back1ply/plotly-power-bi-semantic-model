"""Tests for PbiClient."""

import pytest
from unittest.mock import MagicMock, patch
from infrastructure.pbi_client import PbiClient, PbiClientConfig
from domain import QueryError


class TestPbiClient:
    @pytest.fixture
    def mock_provider(self):
        mock = MagicMock()
        mock.get_token.return_value = "fake-token"
        return mock

    @pytest.fixture
    def mock_limiter(self):
        return MagicMock()

    @pytest.fixture
    def config(self):
        return PbiClientConfig(
            workspace_id="test-workspace",
            dataset_id="test-dataset",
            api_base="https://api.powerbi.com"
        )

    @pytest.fixture
    def client(self, mock_provider, mock_limiter, config):
        return PbiClient(
            token_provider=mock_provider,
            rate_limiter=mock_limiter,
            config=config
        )

    def test_query_success(self, client, mock_limiter):
        """query() successfully executes DAX and cleans column names."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [{"tables": [{"rows": [{"'Sales'[Amount]": 100}]}]}]
        }

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = client.query("EVALUATE TOPN(1, 'Sales')")

            assert result == [{"Amount": 100}]
            mock_limiter.enforce_rate_limit.assert_called_once()
            mock_post.assert_called_once()
            # Verify request body contains correct dataset/workspace
            args, kwargs = mock_post.call_args
            assert "test-dataset" in args[0]
            assert kwargs["json"]["queries"][0]["query"] == "EVALUATE TOPN(1, 'Sales')"

    @pytest.mark.parametrize("bad_status", [400, 401, 403, 404, 500])
    def test_query_api_errors(self, client, bad_status):
        """query() raises QueryError for various non-OK HTTP statuses."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = bad_status
        mock_response.text = f"Error {bad_status}"

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match=f"Power BI query failed \({bad_status}\)"):
                client.query("EVALUATE Table")

    @pytest.mark.parametrize("raw_name, clean_name", [
        ("'Table'[Column]", "Column"),
        ("Table[Column]", "Column"),
        ("[Column]", "Column"),
        ("NoBrackets", "NoBrackets"),
        ("'Escaped Table'[Sales Amount]", "Sales Amount"),
    ])
    def test_column_cleaning_logic(self, client, raw_name, clean_name):
        """Verify regex cleaning of various PBI column naming formats."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [{"tables": [{"rows": [{raw_name: 1}]}]}]
        }

        with patch("requests.post", return_value=mock_response):
            result = client.query("EVALUATE T")
            assert list(result[0].keys()) == [clean_name]

    def test_query_empty_results(self, client):
        """query() handles responses with no rows gracefully."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [{"tables": [{"rows": []}]}]
        }

        with patch("requests.post", return_value=mock_response):
            result = client.query("EVALUATE EmptyTable")
            assert result == []

    def test_query_malformed_json(self, client):
        """query() raises QueryError if API returns non-JSON content."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match="Power BI response parsing failure"):
                client.query("EVALUATE Table")
