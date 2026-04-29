import asyncio
from playwright.async_api import async_playwright


async def capture_dash_errors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        captured_events = []
        page.on(
            "console",
            lambda msg: captured_events.append({"type": f"console_{msg.type}", "text": msg.text}),
        )
        page.on(
            "requestfailed",
            lambda request: captured_events.append(
                {
                    "type": "request_failed",
                    "text": f"{request.url}: {request.failure.error_text if request.failure else 'Unknown error'}",
                }
            ),
        )
        page.on(
            "response",
            lambda response: (
                captured_events.append(
                    {
                        "type": "response_error",
                        "text": f"{response.url}: {response.status}",
                    }
                )
                if response.status >= 400
                else None
            ),
        )

        paths = ["/", "/schema", "/model"]
        for path in paths:
            print(f"\n--- Checking {path} ---")
            try:
                await page.goto(
                    f"http://127.0.0.1:8050{path}",
                    wait_until="networkidle",
                    timeout=30000,
                )
                await asyncio.sleep(5)

                error_selectors = [
                    ".dash-debug-menu--error",
                    ".dash-fe-error__button",
                    ".dash-debug-menu",
                ]
                found_error = False
                for selector in error_selectors:
                    if (
                        await page.locator(selector).count() > 0
                        and await page.locator(selector).is_visible()
                    ):
                        print(f"Found debug element on {path} with selector: {selector}")
                        found_error = True
                        if "error" in selector or "fe-error" in selector:
                            await page.locator(selector).click()
                            await asyncio.sleep(1)
                            errors = page.locator(
                                ".dash-debug-menu--errors-container, .dash-fe-error__content"
                            )
                            if await errors.is_visible():
                                error_text = await errors.inner_text()
                                print(f"Captured Debug Errors on {path}:\n{error_text}")

                if not found_error:
                    print(f"No Dash Debug Menu element found on {path}.")
            except Exception as e:
                print(f"Failed to check {path}: {e}")

        print("\nCaptured Events (All Console + Errors):")
        for event in captured_events:
            print(f"[{event['type']}] {event['text']}")

        await page.screenshot(path="scripts/output/debug_screenshot.png", full_page=True)
        print("Screenshot saved to scripts/output/debug_screenshot.png")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_dash_errors())
