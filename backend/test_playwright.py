import asyncio
from playwright.async_api import async_playwright

async def test_medidas():
    print("Testing Medidas Correctivas...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx", timeout=30000)
            await page.wait_for_timeout(5000)
            await page.screenshot(path="medidas_test.png", full_page=True)
            print("Content measures:", (await page.content())[:200])
        except Exception as e:
            print("Error Medidas:", e)
        finally:
            await browser.close()

async def test_judiciales():
    print("\nTesting Antecedentes Judiciales...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        try:
            await page.goto("https://antecedentes.policia.gov.co:7005/WebJudicial/", timeout=30000)
            await page.wait_for_timeout(5000)
            await page.screenshot(path="judiciales_test.png", full_page=True)
            
            # Find the radio button containing 'Acepto'
            print("Trying to click Acepto...")
            await page.locator("text=Acepto").first.click()
            await page.locator("text=Enviar").first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path="judiciales_test_after.png", full_page=True)
        except Exception as e:
            print("Error Judiciales:", e)
        finally:
            await browser.close()

async def test_fiscales():
    print("\nTesting Antecedentes Fiscales...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://www.contraloria.gov.co/web/guest/persona-natural", timeout=30000)
            await page.wait_for_timeout(10000)
            await page.screenshot(path="fiscales_test.png", full_page=True)
            
            frames = page.frames
            print(f"Found {len(frames)} frames")
            for i, f in enumerate(frames):
                print(f"Frame {i}: {f.url}")
                if "certificado" in f.url.lower() or "cgr" in f.url.lower():
                    print("Found interesting frame")
        except Exception as e:
            print("Error Fiscales:", e)
        finally:
            await browser.close()

async def run_all():
    await test_medidas()
    await test_judiciales()
    await test_fiscales()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_all())
