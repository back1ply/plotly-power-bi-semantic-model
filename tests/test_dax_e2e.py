import pytest
from playwright.sync_api import Page, expect
import os
import time

# This test assumes the app is running on http://127.0.0.1:8050
# Use $env:RUN_UI_TESTS=1; pytest tests/test_dax_e2e.py to run
BASE_URL = "http://127.0.0.1:8050"
DAX_URL = f"{BASE_URL}/dax"

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1")
def test_dax_page_full_workflow(page: Page):
    """E2E test covering the complete DAX query workflow."""
    
    # 1. Load Page
    page.goto(DAX_URL)
    page.wait_for_load_state("networkidle")
    
    # 2. Verify Model Explorer & Field Insertion
    # Expand first table
    accordion_control = page.locator(".mantine-Accordion-control").first
    expect(accordion_control).to_be_visible()
    accordion_control.click()
    
    # Find a column badge
    badge = page.locator(".mantine-Badge-root").first
    badge_text = badge.inner_text()
    badge.click()
    
    # Verify insertion in Ace Editor
    editor_content = page.locator(".ace_content").first
    expect(editor_content).to_contain_text(badge_text, ignore_case=True)
    
    # 3. Clear Editor
    page.get_by_role("button", name="Clear").click()
    # Wait for Ace to clear (internal update)
    time.sleep(1)
    expect(editor_content).not_to_have_text(badge_text, ignore_case=True)
    
    # 4. Execute Valid Query & Verify Grid
    editor_input = page.locator("#dax-editor .ace_text-input")
    editor_input.focus()
    query = 'EVALUATE ROW("TestColumn", 12345)'
    page.keyboard.type(query)
    
    page.get_by_role("button", name="Execute").click()
    
    # Check Status
    status = page.locator("#dax-query-status")
    expect(status).to_contain_text("✓ 1 rows", timeout=10000)
    
    # Check Grid Results
    row = page.locator(".ag-row").first
    expect(row).to_be_visible()
    expect(row).to_contain_text("12345")
    
    # 5. Test Formatting
    page.get_by_role("button", name="Clear").click()
    # Wait for both editor and status to reset
    time.sleep(2)
    expect(status).to_have_text("Ready")
    
    page.locator("#dax-editor .ace_text-input").focus()
    page.keyboard.type("EVALUATE,SUMMARIZECOLUMNS('Table'[Col])")
    time.sleep(2)
    page.get_by_role("button", name="Format").click()
    
    # Format status should appear
    expect(status).to_contain_text("Formatted", timeout=15000)
    # Verify structure (should have multiple lines now)
    # In Ace, if it's one line it's one div. If it's formatted it should be more.
    assert page.locator(".ace_line").count() > 1

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1")
def test_dax_page_error_handling(page: Page):
    """Verify that the page handles DAX errors gracefully."""
    page.goto(DAX_URL)
    page.wait_for_load_state("networkidle")
    
    editor_input = page.locator("#dax-editor .ace_text-input")
    editor_input.focus()
    # Invalid DAX syntax
    page.keyboard.type("NOT_A_KEYWORD 'Table'")
    
    page.get_by_role("button", name="Execute").click()
    
    status = page.locator("#dax-query-status")
    expect(status).to_contain_text("✗ Query must begin with EVALUATE or DEFINE.")
    
    # Invalid Power BI Query
    page.get_by_role("button", name="Clear").click()
    time.sleep(1) 
    editor_input.focus()
    page.keyboard.type("EVALUATE 'NonExistentTable'")
    time.sleep(1) 
    page.get_by_role("button", name="Execute").click()
    
    expect(status).to_contain_text("✗ Power BI query failed", timeout=10000)
