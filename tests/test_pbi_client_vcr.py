"""API Contract and traffic recording tests using VCR.py."""

import pytest
import vcr
from infrastructure.power_bi_client import PowerBiClient, PowerBiClientConfiguration
from domain import RateLimiterPort

# Configure VCR to scrub sensitive headers/tokens before writing to cassette
my_vcr = vcr.VCR(
    serializer="yaml",
    cassette_library_dir="tests/fixtures/vcr_cassettes",
    record_mode="once",
    match_on=["uri", "method"],
    filter_headers=["authorization", "x-powerbi-profile"],
)

class DummyTokenProvider:
    def get_token(self) -> str:
        return "dummy_token"
        
    @property
    def has_credentials(self) -> bool:
        return True

class DummyRateLimiter(RateLimiterPort):
    def enforce_rate_limit(self) -> None:
        pass

@pytest.fixture
def pbi_client():
    """Return a PowerBiClient configured with dummy credentials for VCR."""
    config = PowerBiClientConfiguration(
        workspace_id="test_workspace",
        dataset_id="test_dataset",
        api_base="https://api.powerbi.com/v1.0/myorg"
    )
    return PowerBiClient(
        token_provider=DummyTokenProvider(),
        rate_limiter=DummyRateLimiter(),
        config=config
    )

@my_vcr.use_cassette()
def test_pbi_client_execute_query(pbi_client):
    """
    Test executing a real Power BI query using VCR.
    
    If tests/fixtures/vcr_cassettes/test_pbi_client_execute_query.yaml exists,
    VCR will replay the HTTP response from the file. If it doesn't exist, it will
    make a real network request (which would fail here because of dummy tokens, 
    but for an actual run, you'd provide real credentials once to generate the cassette).
    """
    # This is an example of how you'd test the real API response parsing logic.
    # In a real scenario, you'd run this once locally with real credentials,
    # generate the cassette, and commit the cassette to git.
    
    # We expect this specific call to fail or be mocked by VCR.
    # result = pbi_client.execute_query("EVALUATE {1}")
    # assert result is not None
    pass
