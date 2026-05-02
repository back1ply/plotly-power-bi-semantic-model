import polars as pl
import pytest
import polars.testing as pl_testing
from unittest.mock import MagicMock, patch
from infrastructure.power_bi_client import PowerBiClient, PowerBiClientConfiguration
from domain import QueryError


class TestPowerBiClient:
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
        return PowerBiClientConfiguration(
            workspace_id="test-workspace",
            dataset_id="test-dataset",
            api_base="https://api.powerbi.com"
        )

    @pytest.fixture
    def client(self, mock_provider, mock_limiter, config):
        return PowerBiClient(
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

            expected = pl.DataFrame([{"Amount": 100}])
            # Unwrap the adapter for comparison (CA-002)
            pl_testing.assert_frame_equal(result._df, expected)
            mock_post.assert_called_once()
            mock_limiter.enforce_rate_limit.assert_called_once()

    def test_query_json_level_error(self, client):
        """query() raises QueryError if Power BI returns 200 OK but includes an error in results."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [{"error": {"message": "DAX Syntax Error"}}]
        }

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match="DAX Syntax Error"):
                client.query("EVALUATE BadQuery")

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
            assert list(result.columns) == [clean_name]

    def test_query_empty_results(self, client):
        """query() handles responses with no rows gracefully."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [{"tables": [{"rows": []}]}]
        }

        with patch("requests.post", return_value=mock_response):
            result = client.query("EVALUATE EmptyTable")
            assert result.is_empty()

    def test_query_malformed_json(self, client):
        """query() raises QueryError if API returns non-JSON content."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(QueryError, match="Power BI response parsing failure"):
                client.query("EVALUATE Table")
