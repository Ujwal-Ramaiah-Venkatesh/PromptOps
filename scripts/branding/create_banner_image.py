"""
Convert HTML banner to PNG image using Playwright
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def html_to_png():
    """Convert the HTML banner to PNG"""
    html_path = os.path.abspath("promptops-banner.html")
    output_path = os.path.abspath("promptops-banner.png")

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1200, 'height': 630})

        # Load HTML file
        await page.goto(f'file:///{html_path}')

        # Wait for animations to settle
        await page.wait_for_timeout(2000)

        # Take screenshot
        await page.screenshot(path=output_path, full_page=False)

        await browser.close()

    print(f"✅ Banner saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    asyncio.run(html_to_png())
