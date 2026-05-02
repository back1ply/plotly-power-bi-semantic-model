"""Power BI Report Embedding Service."""

import logging

import requests

from domain import EmbedConfig
from domain import EmbedPort
from domain import QueryError
from domain import TokenProviderPort

from .power_bi_client import PowerBiClientConfiguration

logger = logging.getLogger(__name__)


class PowerBiEmbedService(EmbedPort):
    """Implementation of report embedding using Power BI REST API. (CA-001)"""

    def __init__(
        self,
        token_provider: TokenProviderPort,
        config: PowerBiClientConfiguration,
    ) -> None:
        """Initialize service with dependencies.

        Args:
            token_provider: Provider for access tokens.
            config: Client configuration settings.
        """
        self._token_provider = token_provider
        self._config = config

    def get_embed_config(self, report_id: str) -> EmbedConfig:
        """Return embed URL and token for a report.

        Args:
            report_id: GUID of the Power BI report to embed.

        Returns:
            EmbedConfig with embedUrl, accessToken, and reportId.

        Raises:
            QueryError: If the REST calls fail.
        """
        token = self._token_provider.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        base = f"{self._config.api_base}/groups/{self._config.workspace_id}"

        try:
            report_resp = requests.get(
                f"{base}/reports/{report_id}",
                headers=headers,
                timeout=self._config.request_timeout,
            )
            if not report_resp.ok:
                raise QueryError(
                    f"Failed to fetch report metadata ({report_resp.status_code}): {report_resp.text}"
                )
            report_data = report_resp.json()
            embed_url: str = report_data["embedUrl"]
            dataset_id: str = report_data.get("datasetId", self._config.dataset_id)

            token_request_body = {"accessLevel": "View", "datasetId": dataset_id}

            token_resp = requests.post(
                f"{base}/reports/{report_id}/GenerateToken",
                json=token_request_body,
                headers=headers,
                timeout=self._config.request_timeout,
            )
            if not token_resp.ok:
                raise QueryError(
                    f"Failed to generate embed token ({token_resp.status_code}): {token_resp.text}"
                )
            embed_token: str = token_resp.json()["token"]
        except Exception as exception:
            if isinstance(exception, QueryError):
                raise
            # Minimal coupling to requests in error reporting
            logger.error("PowerBiEmbedService failure: %s", exception)
            raise QueryError(f"Power BI embedding failure: {exception}") from exception

        return EmbedConfig(
            report_id=report_id,
            embed_url=embed_url,
            access_token=embed_token,
        )
