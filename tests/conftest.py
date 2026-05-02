"""Shared pytest fixtures."""

import os
import sys

# Critical: If PowerBiClient was already imported (by app.py during test collection),
# we need to ensure our mocks are applied. Do this BEFORE any other imports.
if "infrastructure.power_bi_client" in sys.modules:
    # Re-import to get the module
    import importlib

    importlib.reload(sys.modules["infrastructure.power_bi_client"])

import diskcache
import polars as pl
import pytest
from unittest.mock import MagicMock
from domain import KeyPerformanceIndicatorConfig, DataFrame
from infrastructure.adapters import PolarsDataFrameAdapter


@pytest.fixture(autouse=True)
def setup_pbi_mocks(monkeypatch):
    """Auto-apply PBI mocks for all tests to handle app.py import side effects.

    Only applies when real credentials are not available (test environment).
    Tests requiring real credentials should explicitly skip this fixture.
    """
    # Only apply mocks if no real credentials
    has_real_creds = all(
        [
            os.getenv("TENANT_ID"),
            os.getenv("CLIENT_ID"),
            os.getenv("CLIENT_SECRET"),
            os.getenv("WORKSPACE_ID"),
            os.getenv("DATASET_ID"),
        ]
    )

    if not has_real_creds:
        # Set test credentials
        monkeypatch.setenv("TENANT_ID", "test-tenant")
        monkeypatch.setenv("CLIENT_ID", "test-client")
        monkeypatch.setenv("CLIENT_SECRET", "test-secret")
        monkeypatch.setenv("WORKSPACE_ID", "test-workspace")
        monkeypatch.setenv("DATASET_ID", "test-dataset")

        # Mock MSAL and requests
        mock_token_result = {"access_token": "fake-token"}  # nosec B105
        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_for_client.return_value = mock_token_result

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [
                {
                    "tables": [
                        {
                            "rows": [
                                {
                                    "Sales[Revenue]": 100.0,
                                    "Date[CalendarYear]": 2023,
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        def mock_msal_init(client_id, client_credential, authority):
            return mock_msal_app

        def mock_requests_post(*args, **kwargs):
            return mock_response

        monkeypatch.setattr("msal.ConfidentialClientApplication", mock_msal_init)
        monkeypatch.setattr("requests.post", mock_requests_post)

    yield

    # Cleanup: reset cached module state after tests
    if "infrastructure.power_bi_client" in sys.modules:
        import importlib

        importlib.reload(sys.modules["infrastructure.power_bi_client"])


@pytest.fixture
def mock_pbi_response(monkeypatch):
    """Legacy fixture - kept for explicit mocking in specific tests.

    Note: Most tests now use autouse setup_pbi_mocks fixture.
    This fixture can be used to override the default mocking if needed.
    """
    # Already handled by autouse fixture - return mock for compatibility
    return MagicMock()


@pytest.fixture
def mock_cache(tmp_path):
    """Return a diskcache.Cache pointed at a temp directory."""
    return diskcache.Cache(str(tmp_path / ".cache"))


@pytest.fixture
def mock_pbi_client():
    """Mock PbiClient that returns a simple DataFrame."""
    mock = MagicMock()
    mock.query.return_value = pl.DataFrame({"Value": [100000], "Label": ["Revenue"]})
    return mock


@pytest.fixture
def kpi_config():
    """Default KPI configuration for testing."""
    return [
        KeyPerformanceIndicatorConfig("Revenue", "Revenue", lambda v: f"${float(v):,.0f}"),
        KeyPerformanceIndicatorConfig("Profit", "Profit", lambda v: f"${float(v):,.0f}"),
        KeyPerformanceIndicatorConfig("Orders", "Orders", lambda v: f"{int(float(v)):,.0f}"),
        KeyPerformanceIndicatorConfig("Avg Order Value", "AvgOrderValue", lambda v: f"${float(v):,.2f}"),
    ]


@pytest.fixture
def sample_sales_df():
    """Multi-year monthly sales data matching Power BI output shape.
    Includes Fiscal Month Number for YoY alignment (July = 1).
    """
    df = pl.DataFrame(
        {
            "Fiscal Year": [2023, 2023, 2024, 2024],
            "Fiscal Month Number": [1, 7, 1, 7],  # July=1, Jan=7
            "MonthKey": [202207, 202301, 202307, 202401],
            # Use ISO format for Polars compatibility
            "Month": ["2022-07-01", "2023-01-01", "2023-07-01", "2024-01-01"],
            "Revenue": [100000, 150000, 120000, 180000],
            "Category": ["Bikes", "Accessories", "Clothing", "Bikes"],
            "Group": ["North America", "Europe", "Pacific", "North America"],
            "Product": ["Road-150", "Helmet", "Jersey", "Mountain-200"],
            "Profit": [40000, 75000, 120000, 75000],
        }
    )
    return PolarsDataFrameAdapter(df)


@pytest.fixture
def sample_kpi_df():
    """KPI totals row matching Power BI output shape."""
    df = pl.DataFrame(
        {
            "Revenue": [1250000.0],
            "Profit": [340000.0],
            "Orders": [1450],
            "AvgOrderValue": [862.0],
        }
    )
    return PolarsDataFrameAdapter(df)


@pytest.fixture
def sample_category_df():
    df = pl.DataFrame(
        {
            "Category": ["Bikes", "Accessories", "Clothing"],
            "Revenue": [800000, 250000, 200000],
        }
    )
    return PolarsDataFrameAdapter(df)


@pytest.fixture
def sample_territory_df():
    df = pl.DataFrame(
        {
            "Group": ["North America", "Europe", "Pacific"],
            "Revenue": [600000, 400000, 250000],
        }
    )
    return PolarsDataFrameAdapter(df)


@pytest.fixture
def sample_products_df():
    df = pl.DataFrame(
        {
            "Product": ["Road-150", "Mountain-200", "Touring-1000"],
            "Category": ["Bikes", "Bikes", "Bikes"],
            "Revenue": [500000, 400000, 300000],
            "Profit": [200000, 150000, 100000],
        }
    )
    return PolarsDataFrameAdapter(df)
