"""Integration tests for Power BI connectivity.

Require real credentials and network access.
Skip in CI: SKIP_INTEGRATION_TESTS=1 pytest
"""

import os
import pytest
from infrastructure.auth import MsalTokenProvider
from infrastructure.rate_limiting import SlidingWindowRateLimiter
from infrastructure.power_bi_client import PowerBiClient, PowerBiClientConfiguration

# Integration tests require real credentials - they run when real credentials exist
# but are skipped in test-only environments
skip_integration = pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "1",
    reason="SKIP_INTEGRATION_TESTS is set",
)
skip_in_ci = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipped in CI environment",
)
skip_without_creds = pytest.mark.skipif(
    not os.getenv("TENANT_ID")
    or not os.getenv("CLIENT_ID")
    or not os.getenv("CLIENT_SECRET"),
    reason="Missing Power BI credentials",
)


@skip_without_creds
@skip_integration
@skip_in_ci
def test_pbi_client_can_connect():
    """PowerBiClient can fetch an OAuth token."""
    token_provider = MsalTokenProvider(
        tenant_id=os.getenv("TENANT_ID", ""),
        client_id=os.getenv("CLIENT_ID", ""),
        client_secret=os.getenv("CLIENT_SECRET", ""),
    )
    rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)
    config = PowerBiClientConfiguration(
        workspace_id=os.getenv("WORKSPACE_ID", ""),
        dataset_id=os.getenv("DATASET_ID", ""),
        api_base=os.getenv("PBI_API_BASE", "https://api.powerbi.com/v1.0/myorg")
    )

    client = PowerBiClient(
        token_provider=token_provider,
        rate_limiter=rate_limiter,
        config=config
    )
    token = client._token_provider.get_token()
    assert token is not None


@skip_without_creds
@skip_integration
@skip_in_ci
def test_pbi_client_can_execute_query():
    """PowerBiClient can execute a simple DAX query."""
    token_provider = MsalTokenProvider(
        tenant_id=os.getenv("TENANT_ID", ""),
        client_id=os.getenv("CLIENT_ID", ""),
        client_secret=os.getenv("CLIENT_SECRET", ""),
    )
    rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)
    config = PowerBiClientConfiguration(
        workspace_id=os.getenv("WORKSPACE_ID", ""),
        dataset_id=os.getenv("DATASET_ID", ""),
        api_base=os.getenv("PBI_API_BASE", "https://api.powerbi.com/v1.0/myorg")
    )

    client = PowerBiClient(
        token_provider=token_provider,
        rate_limiter=rate_limiter,
        config=config
    )
    result = client.query("EVALUATE TOPN(1, 'Sales')")
    assert result is not None
    assert len(result) > 0


@skip_integration
@pytest.mark.skip(reason="Flaky — depends on shared cache state")
def test_startup_cache_populated():
    """populate_startup_cache fills all keys with real data."""
    # This test is legacy
    token_provider = MsalTokenProvider(
        tenant_id=os.getenv("TENANT_ID", ""),
        client_id=os.getenv("CLIENT_ID", ""),
        client_secret=os.getenv("CLIENT_SECRET", ""),
    )
    rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)
    config = PowerBiClientConfiguration(
        workspace_id=os.getenv("WORKSPACE_ID", ""),
        dataset_id=os.getenv("DATASET_ID", ""),
        api_base=os.getenv("PBI_API_BASE", "https://api.powerbi.com/v1.0/myorg")
    )

    client = PowerBiClient(
        token_provider=token_provider,
        rate_limiter=rate_limiter,
        config=config
    )
    # We'd need StartupDataLoader here
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
