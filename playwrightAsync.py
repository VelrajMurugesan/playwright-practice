from playwright.async_api import async_playwright, Playwright
import asyncio


async def run(playwright: Playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://youtube.com")
    print(await page.title())
    await page.wait_for_timeout(15000)
    await browser.close()

if __name__ == "__main__":
    async def main():
        async with async_playwright() as playwright:
            await run(playwright)
    asyncio.run(main())
