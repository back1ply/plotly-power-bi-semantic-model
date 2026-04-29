import asyncio
from playwright.async_api import async_playwright


async def debug_dash():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Listening for Dash errors...")

        dash_logs = []
        page.on("console", lambda msg: dash_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            await page.goto("http://127.0.0.1:8050/", wait_until="networkidle")
            await asyncio.sleep(10)

            print("\nCaptured Dash/Plotly Logs:")
            for log in dash_logs:
                print(f" > {log}")

            # Check for specific Dash error messages in the DOM
            content = await page.content()
            if "ID not found in layout" in content:
                print("Found: ID not found in layout")
            if "Duplicate ID" in content:
                print("Found: Duplicate ID")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_dash())
