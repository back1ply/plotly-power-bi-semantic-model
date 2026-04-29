"""Power BI REST API Client.

Provides a client for executing DAX queries against Power BI semantic models
using Azure AD service principal authentication.
"""

import logging
from dataclasses import dataclass
from typing import Any

import requests

from domain import QueryClientPort
from domain import QueryError
from domain import RateLimiterPort
from domain import TokenProviderPort

from .adapters import extract_column_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PbiClientConfig:
    """Configuration for Power BI client."""

    workspace_id: str
    dataset_id: str
    api_base: str
    request_timeout: int = 60


class PbiClient(QueryClientPort):
    """Power BI client for executing DAX queries."""

    def __init__(
        self,
        token_provider: TokenProviderPort,
        rate_limiter: RateLimiterPort,
        config: PbiClientConfig,
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

    def _handle_api_error(self, exc: Exception, context: str) -> QueryError:
        """Centralized error handling for API failures. (OO-002)"""
        if isinstance(exc, QueryError):
            return exc

        # Determine if it's likely a network/library-level error without direct coupling
        exc_type_name = type(exc).__name__
        exc_module = getattr(type(exc), "__module__", "")
        
        # Log the specific error for internal debugging
        logger.error("PbiClient.%s failure [%s]: %s", context, exc_type_name, exc)

        # 1. Handle Network/Connection issues (e.g., requests.exceptions.RequestException)
        if "requests" in exc_module or "Connection" in exc_type_name or "Timeout" in exc_type_name:
            return QueryError(f"Power BI network or connection failure during {context}")

        # 2. Handle Data/Parsing issues
        if isinstance(exc, (ValueError, KeyError)):
            return QueryError(f"Power BI response parsing failure during {context}")

        # 3. Fallback for other unexpected errors
        return QueryError(f"Unexpected Power BI error during {context}")

    def _execute_query(self, dax: str) -> list[dict[str, Any]]:
        token = self._token_provider.get_token()

        try:
            resp = requests.post(
                f"{self._config.api_base}/groups/{self._config.workspace_id}/datasets/{self._config.dataset_id}/executeQueries",
                json={
                    "queries": [{"query": dax}],
                    "serializerSettings": {"includeNulls": True},
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=self._config.request_timeout,
            )
            if not resp.ok:
                raise QueryError(
                    message=f"Power BI query failed ({resp.status_code}): {resp.text}",
                )

            data = resp.json()
        except Exception as exc:
            raise self._handle_api_error(exc, "_execute_query") from exc

        results = data.get("results", [])
        if not results:
            return []

        tables = results[0].get("tables", [])
        if not tables:
            return []

        rows = tables[0].get("rows", [])
        if not rows:
            return []

        return [{extract_column_name(k): v for k, v in row.items()} for row in rows]

    def query(self, dax: str) -> list[dict[str, Any]]:
        """Execute DAX query against the configured dataset."""
        self._rate_limiter.enforce_rate_limit()
        records = self._execute_query(dax)
        logger.info("PbiClient.query: returned %d rows", len(records))
        return records
