import asyncio
from playwright.async_api import async_playwright

async def get_medidas_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx", timeout=30000)
            await page.wait_for_timeout(3000)
            html = await page.content()
            with open("medidas_body.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print("Error Medidas:", e)
        finally:
            await browser.close()

async def get_judiciales_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        try:
            await page.goto("https://antecedentes.policia.gov.co:7005/WebJudicial/", timeout=30000)
            await page.wait_for_timeout(3000)
            html = await page.content()
            with open("judiciales_body.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print("Error Judiciales:", e)
        finally:
            await browser.close()

async def get_fiscales_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://www.contraloria.gov.co/web/guest/persona-natural", timeout=30000)
            await page.wait_for_timeout(5000)
            frames = page.frames
            for f in frames:
                if "certificado" in f.url.lower() or "cgr" in f.url.lower():
                    html = await f.content()
                    with open("fiscales_frame.html", "w", encoding="utf-8") as file:
                        file.write(html)
        except Exception as e:
            print("Error Fiscales:", e)
        finally:
            await browser.close()

async def run_all():
    await get_medidas_html()
    await get_judiciales_html()
    await get_fiscales_html()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_all())
