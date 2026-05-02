"""Authentication.

Provides token providers for Power BI authentication.
"""

import logging

from msal import ConfidentialClientApplication

from domain import AuthenticationError
from domain import TokenProviderPort

logger = logging.getLogger(__name__)


class MsalTokenProvider(TokenProviderPort):
    """Provides authentication tokens for Power BI using MSAL."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str) -> None:
        """Initialize with credentials. Does not perform I/O.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Service principal client ID
            client_secret: Service principal client secret
        """
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._msal_app: ConfidentialClientApplication | None = None

    @property
    def has_credentials(self) -> bool:
        """Check if provider is configured with credentials."""
        return all([self._tenant_id, self._client_id, self._client_secret])

    def _initialize(self) -> None:
        """Initialize MSAL application lazily."""
        if self._msal_app is not None:
            return

        if not self.has_credentials:
            raise AuthenticationError("MsalTokenProvider: missing credentials")

        try:
            self._msal_app = ConfidentialClientApplication(
                client_id=self._client_id,
                client_credential=self._client_secret,
                authority=f"https://login.microsoftonline.com/{self._tenant_id}",
            )
        except Exception as exception:
            logger.error("MsalTokenProvider._initialize failed: %s", exception)
            raise AuthenticationError(f"Failed to initialize MSAL: {exception}") from exception

    def get_token(self) -> str:
        """Acquire and return an access token, initializing MSAL if needed."""
        self._initialize()
        assert self._msal_app is not None

        try:
            result = self._msal_app.acquire_token_for_client(
                scopes=["https://analysis.windows.net/powerbi/api/.default"]
            )
            token = result.get("access_token") if isinstance(result, dict) else None
            if not token:
                error_desc = (
                    result.get("error_description") if isinstance(result, dict) else "Unknown"
                )
                raise AuthenticationError(
                    f"Could not acquire token for tenant {self._tenant_id}: {error_desc}"
                )
            return token
        except Exception as exception:
            if isinstance(exception, AuthenticationError):
                raise
            logger.error("MSAL Auth Provider retrieval failed: %s", exception)
            raise AuthenticationError(f"Failed to acquire token: {exception}") from exception
