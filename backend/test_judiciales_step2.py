import asyncio
from playwright.async_api import async_playwright

async def get_judiciales_step2():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        try:
            await page.goto("https://antecedentes.policia.gov.co:7005/WebJudicial/", timeout=30000)
            await page.locator("label[for='aceptaOption:0']").click()
            
            # Wait for primefaces to enable the button
            btn = page.locator("#continuarBtn")
            await btn.wait_for(state="attached")
            
            # Ensure it's not disabled
            for _ in range(20):
                disabled = await btn.get_attribute("disabled")
                if not disabled: break
                await page.wait_for_timeout(500)
                
            await btn.click()
            await page.wait_for_url("**/antecedentes.xhtml", timeout=15000)
            await page.wait_for_load_state("networkidle")
            
            html = await page.content()
            with open("judiciales_step2.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print("Error Judiciales 2:", e)
        finally:
            await browser.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(get_judiciales_step2())
