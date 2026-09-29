import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await page.goto("https://www.google.com/search?q=flights+from+DEL+to+BOM+on+2026-09-20&hl=en")
        await page.wait_for_timeout(5000)
        content = await page.content()
        print("Length:", len(content))
        with open("search_result.html", "w") as f:
            f.write(content)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
