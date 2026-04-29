import pytest
from playwright.sync_api import Page, expect
import time
import subprocess  # nosec B404
import os

# This test requires the app to be running. 
# In a CI environment, we'd start/stop the server in a fixture.
# For now, we'll assume the server is running on http://127.0.0.1:8050

BASE_URL = "http://127.0.0.1:8050"

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1 to run Playwright UI tests")
def test_dashboard_initial_load(page: Page):
    """Verify the dashboard loads with correct title and no console errors."""
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Check Title (Specific to Heading role)
    expect(page.get_by_role("heading", name="Executive Summary")).to_be_visible()
    expect(page.get_by_text("Sales Dashboard")).to_be_visible()
    
    # Verify no console errors
    assert len(console_errors) == 0, f"Console had errors: {console_errors}"

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1 to run Playwright UI tests")
def test_dax_inspector_interaction(page: Page):
    """Verify that clicking the DAX button opens the drawer with content."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Find the first DAX button and click it
    dax_button = page.locator("button[id*='open-dax-inspector']").first
    expect(dax_button).to_be_visible()
    dax_button.click()
    
    # In Mantine v7/DMC v2, the drawer might be rendered in a Portal
    # We wait for the specific ID of the code block inside it
    code_content = page.locator("#dax-inspector-content")
    expect(code_content).to_be_visible(timeout=10000)
    
    # Check if code content is populated
    expect(code_content).not_to_have_text("Select a chart to view its DAX query", timeout=10000)
    # Most DAX queries in this app will contain EVALUATE or FILTER
    expect(code_content).to_contain_text("SUMMARIZECOLUMNS")

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1 to run Playwright UI tests")
def test_mobile_responsiveness(page: Page):
    """Verify layout adjustments for mobile viewports."""
    page.set_viewport_size({"width": 390, "height": 844})
    
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    
    # Check if the main title is visible
    expect(page.get_by_role("heading", name="Executive Summary")).to_be_visible()

if __name__ == "__main__":
    # Instruction for manual run
    print("To run these tests, ensure the app is running and execute:")
    print("$env:RUN_UI_TESTS=1; pytest tests/test_ui_interactive.py --browser chromium --headed")
