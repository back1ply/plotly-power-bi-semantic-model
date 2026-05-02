"""End-to-End integration tests using Playwright and Dash."""

import os
import threading
import time
import pytest
from playwright.sync_api import Page, expect
from app import create_app
from dependency_injection import DiContainer
from config import AppConfig

# Use a fixed port for E2E tests
E2E_PORT = 8051
E2E_URL = f"http://127.0.0.1:{E2E_PORT}"

@pytest.fixture(scope="module")
def dash_server():
    """Start the Dash app in a background thread."""
    config = AppConfig()
    # Ensure we use a clean container with mockable dependencies
    container = DiContainer(config)
    
    app = create_app(container=container, should_preload=False)
    
    # Run server in thread
    thread = threading.Thread(
        target=lambda: app.run(
            debug=False, 
            port=E2E_PORT, 
            host="127.0.0.1"
        ),
        daemon=True
    )
    thread.start()
    
    # Wait for server to start
    time.sleep(3)
    yield E2E_URL

def test_e2e_home_to_dax_inspector(dash_server, page: Page):
    """Verify that the home page loads and the DAX inspector works."""
    page.goto(dash_server)
    
    # 1. Verify Home Page loads
    expect(page.get_by_role("heading", name="Executive Summary")).to_be_visible(timeout=20000)
    
    # 2. Open DAX Inspector
    # Find the first ActionIcon for the DAX inspector (identified by type in ID)
    dax_btn = page.locator("button[id*='open-dax-inspector']").first
    expect(dax_btn).to_be_visible()
    dax_btn.click()
    
    # 3. Verify Code is present in drawer
    # Mantine Drawer content
    inspector_content = page.locator("#dax-inspector-content")
    expect(inspector_content).to_be_visible()
    # Initial placeholder or real query
    expect(inspector_content).not_to_have_text("Select a chart")

def test_e2e_navigation_to_schema(dash_server, page: Page):
    """Verify that we can navigate to the Schema page."""
    page.goto(dash_server)
    
    # Click on 'Data Model Schema' link in Sidebar
    schema_link = page.get_by_role("link", name="Data Model Schema")
    expect(schema_link).to_be_visible()
    schema_link.click()
    
    # Verify we are on the Schema page
    expect(page.get_by_role("heading", name="Data Model Schema")).to_be_visible()
    # Verify accordion exists
    expect(page.locator(".mantine-Accordion-root")).to_be_visible()
