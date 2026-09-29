import asyncio
from playwright.async_api import async_playwright
import re
from datetime import date, timedelta

async def test_scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        page = await context.new_page()
        
        origin = "DEL"
        destination = "BOM"
        travel_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{travel_date}%20oneway"
        print(f"Scraping: {url}")
        
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        
        prices = re.findall(r'₹[\s]*([0-9,]+)', content)
        print("Raw found prices:", prices)
        
        if prices:
            prices = [int(p.replace(',', '').strip()) for p in prices]
            prices = [p for p in prices if p > 1500 and p < 200000]
            print("Filtered realistic prices:", prices[:5])
        else:
            print("No prices found using regex.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrape())
