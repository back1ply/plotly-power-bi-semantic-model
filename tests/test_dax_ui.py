import pytest
from playwright.sync_api import Page, expect
import os

BASE_URL = "http://127.0.0.1:8050"
DAX_URL = f"{BASE_URL}/dax"

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1")
def test_dax_page_explorer_insert(page: Page):
    """Verify that clicking a field in the Model Explorer inserts it into the editor."""
    page.goto(DAX_URL)
    page.wait_for_load_state("networkidle")
    
    # Expand first table in explorer
    accordion_control = page.locator(".mantine-Accordion-control").first
    accordion_control.click()
    
    # Find a badge (column or measure)
    badge = page.locator(".mantine-Badge-root").first
    badge_text = badge.inner_text()
    
    # Click the badge to insert
    badge.click()
    
    # Check Ace Editor content
    editor_content = page.locator(".ace_content").first
    expect(editor_content).to_contain_text(badge_text, ignore_case=True)

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1")
def test_dax_page_clear_button(page: Page):
    """Verify that the Clear button empties the editor."""
    page.goto(DAX_URL)
    page.wait_for_load_state("networkidle")
    
    editor = page.locator(".ace_text-input")
    editor.focus()
    page.keyboard.type("EVALUATE 'Sales'")
    
    # Click Clear
    page.get_by_role("button", name="Clear").click()
    
    # Check if cleared
    editor_content = page.locator(".ace_content").first
    expect(editor_content).not_to_have_text("EVALUATE 'Sales'")

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1")
def test_dax_page_copy_status(page: Page):
    """Verify that clicking Copy updates the status."""
    page.goto(DAX_URL)
    page.wait_for_load_state("networkidle")
    
    page.get_by_role("button", name="Copy").click()
    
    status = page.locator("#dax-query-status")
    expect(status).to_have_text("Copied!")

@pytest.mark.skipif(not os.environ.get("RUN_UI_TESTS"), reason="Set RUN_UI_TESTS=1")
def test_dax_page_format_button(page: Page):
    """Verify that the Format button updates the content and status."""
    page.goto(DAX_URL)
    page.wait_for_load_state("networkidle")
    
    editor = page.locator(".ace_text-input")
    editor.focus()
    # Unformatted query
    page.keyboard.type("EVALUATE,SUMMARIZECOLUMNS('T'[C])")
    
    page.get_by_role("button", name="Format").click()
    
    editor_content = page.locator(".ace_content").first
    expect(editor_content).to_contain_text("EVALUATE")
    
    status = page.locator("#dax-query-status")
    expect(status).to_have_text("✓ Formatted")
