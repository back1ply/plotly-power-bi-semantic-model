"""Power BI REST API Client.

Provides a client for executing DAX queries against Power BI semantic models
using Azure AD service principal authentication.
"""

import logging
from dataclasses import dataclass

import polars as pl
import requests

from domain import clean_dax_query
from domain import DataFrame
from domain import QueryClientPort
from domain import QueryError
from domain import RateLimiterPort
from domain import TokenProviderPort

from .utils import PowerBiResponseParser

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PowerBiClientConfiguration:
    """Configuration for Power BI client."""

    workspace_id: str
    dataset_id: str
    api_base: str
    request_timeout: int = 60


class PowerBiClient(QueryClientPort):
    """Power BI client for executing DAX queries."""

    def __init__(
        self,
        token_provider: TokenProviderPort,
        rate_limiter: RateLimiterPort,
        config: PowerBiClientConfiguration,
    ) -> None:
        """Initialize client with dependencies and configuration.

        Args:
            token_provider: Provider for access tokens.
            rate_limiter: Limiter for API requests.
            config: Client configuration settings.
        """
        self._token_provider = token_provider
        self._rate_limiter = rate_limiter
        self._config = config

    @property
    def has_credentials(self) -> bool:
        """Check if client is configured with credentials."""
        return self._token_provider.has_credentials

    def _handle_api_error(self, exception: Exception, context: str) -> QueryError:
        """Centralized error handling for API failures. (OO-003)"""
        if isinstance(exception, QueryError):
            return exception

        # Log the specific error for internal debugging
        logger.error("PowerBiClient.%s failure: %s", context, exception)

        # 1. Handle Network/Connection issues explicitly using requests exceptions
        if isinstance(exception, requests.exceptions.RequestException):
            return QueryError(f"Power BI network or connection failure during {context}")

        # 2. Handle Data/Parsing issues
        if isinstance(exception, (ValueError, KeyError)):
            return QueryError(f"Power BI response parsing failure during {context}: {exception}")

        # 3. Fallback for other unexpected errors
        return QueryError(f"Unexpected Power BI error during {context}")

    def _execute_query(self, dax_query: str) -> DataFrame:
        token = self._token_provider.get_token()

        try:
            response = requests.post(
                f"{self._config.api_base}/groups/{self._config.workspace_id}/datasets/{self._config.dataset_id}/executeQueries",
                json={
                    "queries": [{"query": dax_query}],
                    "serializerSettings": {"includeNulls": True},
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=self._config.request_timeout,
            )
            if not response.ok:
                raise QueryError(
                    message=f"Power BI query failed ({response.status_code}): {response.text}",
                )

            data = response.json()
            records = PowerBiResponseParser.parse_execute_queries_response(data)
            from .adapters import PolarsDataFrameAdapter
            return PolarsDataFrameAdapter(pl.DataFrame(records))
        except Exception as exception:
            raise self._handle_api_error(exception, "_execute_query") from exception

    def query(self, dax_query: str) -> DataFrame:
        """Execute DAX query against the configured dataset."""
        self._rate_limiter.enforce_rate_limit()
        # Automatically clean user-supplied DAX to remove invisible characters (OO-004)
        cleaned_query = clean_dax_query(dax_query)
        data_frame = self._execute_query(cleaned_query)
        logger.info("PowerBiClient.query: returned %d rows", len(data_frame))
        return data_frame
