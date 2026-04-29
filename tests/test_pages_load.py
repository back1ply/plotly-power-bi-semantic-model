import pytest
try:
    from playwright.sync_api import Page, expect
except ImportError:
    # Playwright not installed, will be skipped by marker
    pass
import time
import os

# Base URL for the running app
BASE_URL = "http://127.0.0.1:8050"

skip_ui = pytest.mark.skipif(
    os.getenv("RUN_UI_TESTS") != "1",
    reason="Set RUN_UI_TESTS=1 to run Playwright UI tests"
)

@skip_ui
@pytest.mark.parametrize("path", ["/", "/model", "/schema"])
def test_page_loads_without_errors(page: "Page", path):
    """
    Automated safety check:
    1. Navigates to every defined route.
    2. Captures browser console for errors (like JavaScript crashes).
    3. Scans page content for 'Callback error' or 'Traceback' text.
    """
    console_errors = []
    
    # Listener to capture console errors
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    
    # Navigate to the page
    page.goto(f"{BASE_URL}{path}")
    
    # Wait for Dash to finish rendering and initial callbacks
    page.wait_for_load_state("networkidle")
    time.sleep(1) # Extra buffer for Dash hydration
    
    # 1. Check for console errors
    assert len(console_errors) == 0, f"Console errors detected on {path}: {console_errors}"
    
    # 2. Check for Dash-specific 'Callback error' or Python Tracebacks in the UI
    content = page.content()
    assert "Callback error" not in content, f"Dash Callback error detected on {path}"
    assert "Traceback (most recent call last)" not in content, f"Python Traceback detected on UI of {path}"
    
    # 3. Verify main content container exists
    # Dash pages usually render into _pages_content or similar
    expect(page.locator("body")).not_to_be_empty()
