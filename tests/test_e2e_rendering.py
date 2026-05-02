import pytest
from playwright.sync_api import Page, expect
import time

@pytest.mark.e2e
def test_dax_query_rendering(page: Page):
    """Verify that a DAX query executes and renders data in the AG Grid."""
    # 1. Navigate to the DAX page
    # Note: Assumes the app is running on http://127.0.0.1:8050
    page.goto("http://127.0.0.1:8050/dax")
    page.wait_for_load_state("networkidle")
    
    # 2. Clear the editor
    page.get_by_role("button", name="Clear").click()
    
    # 3. Enter a valid query
    query = "EVALUATE SUMMARIZECOLUMNS('Product'[Category], \"Revenue\", [Revenue])"
    # Wait for editor to be ready and sync via blur to ensure Dash picks it up
    page.wait_for_selector(".ace_editor")
    page.evaluate(f"window._daxAceEditor.setValue({repr(query)}); window._daxAceEditor.blur();")
    time.sleep(0.5) # Allow Dash state to sync
    
    # 4. Execute
    page.get_by_role("button", name="Execute").click()
    
    # 5. Wait for success status
    # Success status starts with a checkmark
    status = page.locator("#dax-query-status")
    expect(status).to_contain_text("✓")
    
    # 6. Verify AG Grid Rendering
    grid = page.locator("#dax-query-results")
    expect(grid).to_be_visible()
    
    # Check that rows are actually rendered in the DOM
    rows = page.locator(".ag-row")
    expect(rows).to_have_count(4) # Based on AdventureWorks categories
    
    # Verify content of the first row
    # Components is the first category in AdventureWorks
    expect(rows.first).to_contain_text("Components")
    
    # 7. Check Visibility (Computed Style)
    # Ensure it's not hidden by missing CSS or zero height
    is_visible_styled = page.evaluate("""
        () => {
            const el = document.querySelector('.ag-header-cell');
            if (!el) return false;
            const style = window.getComputedStyle(el);
            return style.visibility !== 'hidden' && parseFloat(style.height) > 0;
        }
    """)
    assert is_visible_styled, "AG Grid headers are hidden or have 0 height"

@pytest.mark.e2e
def test_dax_sanitization_e2e(page: Page):
    """Verify that queries with invisible characters are handled correctly in the UI."""
    page.goto("http://127.0.0.1:8050/dax")
    page.get_by_role("button", name="Clear").click()
    
    # Query with leading Zero-Width Space
    query = "\u200bEVALUATE ROW(\"Value\", 1)"
    page.wait_for_selector(".ace_editor")
    page.evaluate(f"window._daxAceEditor.setValue({repr(query)}); window._daxAceEditor.blur();")
    time.sleep(0.5)
    
    page.get_by_role("button", name="Execute").click()
    
    # If sanitization works, it should succeed
    status = page.locator("#dax-query-status")
    expect(status).to_contain_text("✓")
    expect(page.locator(".ag-row")).to_have_count(1)
