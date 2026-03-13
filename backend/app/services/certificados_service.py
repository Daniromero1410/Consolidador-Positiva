"""
Certificados Service - Automatización con Playwright
======================================================

Servicio para consultar certificados gubernamentales usando Playwright:
1. Medidas Correctivas (Policía Nacional - RNMC)
2. Antecedentes Judiciales (Policía Nacional - DIJIN)
3. Antecedentes Fiscales (Contraloría General)

Cada consulta:
- Abre un navegador headless
- Navega a la página oficial
- Llena el formulario
- Captura el resultado como screenshot/PDF
"""

import os
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs", "certificados")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Timeout por página (segundos)
PAGE_TIMEOUT = 30000  # 30s en ms para Playwright


class CertificadosService:
    """Servicio de consulta de certificados con Playwright."""

    # ══════════════════════════════════════════════════════════
    # CONSULTA PRINCIPAL
    # ══════════════════════════════════════════════════════════

    @staticmethod
    async def consultar(
        tipo_documento: str,
        numero_documento: str,
        certificados: list[str]
    ) -> Dict:
        """
        """
        import sys
        
        # Ejecutar en un thread separado con su propio EventLoop (Proactor) que soporta Subprocesos en Windows
        return await asyncio.to_thread(
            CertificadosService._run_playwright_sync,
            tipo_documento, numero_documento, certificados
        )

    @staticmethod
    def _run_playwright_sync(tipo_documento: str, numero_documento: str, certificados: list[str]) -> Dict:
        """Wrapper síncrono que inicializa un ProactorEventLoop nuevo seguro para Windows."""
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Crear nuevo loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                CertificadosService._consultar_async(tipo_documento, numero_documento, certificados)
            )
        finally:
            loop.close()

    @staticmethod
    async def _consultar_async(
        tipo_documento: str,
        numero_documento: str,
        certificados: list[str]
    ) -> Dict:
        """
        Consulta internamente múltiples certificados en paralelo usando Playwright.
        """
        from playwright.async_api import async_playwright

        resultados = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )

            # Ejecutar consultas en paralelo
            tasks = []
            for cert_id in certificados:
                if cert_id == 'medidas':
                    tasks.append(CertificadosService._consultar_medidas_correctivas(
                        browser, tipo_documento, numero_documento
                    ))
                elif cert_id == 'disciplinarios':
                    tasks.append(CertificadosService._consultar_antecedentes_judiciales(
                        browser, tipo_documento, numero_documento
                    ))
                elif cert_id == 'fiscales':
                    tasks.append(CertificadosService._consultar_antecedentes_fiscales(
                        browser, tipo_documento, numero_documento
                    ))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for cert_id, result in zip(certificados, results):
                if isinstance(result, Exception):
                    resultados[cert_id] = {
                        "estado": "error",
                        "mensaje": str(result)[:100]
                    }
                else:
                    resultados[cert_id] = result

            await browser.close()

        return resultados

    # ══════════════════════════════════════════════════════════
    # 1. MEDIDAS CORRECTIVAS (Policía Nacional)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    async def _consultar_medidas_correctivas(
        browser, tipo_documento: str, numero_documento: str
    ) -> Dict:
        """
        Consulta en: https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx
        
        Flujo:
        1. Navegar → aceptar modal de términos
        2. Seleccionar tipo documento
        3. Ingresar número
        4. Click consultar
        5. Capturar resultado
        """
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            await page.goto(
                'https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx',
                wait_until='networkidle',
                timeout=PAGE_TIMEOUT
            )

            # Aceptar modal si aparece
            try:
                modal_btn = page.locator('#ContentPlaceHolder3_btn_salir_modal')
                if await modal_btn.is_visible(timeout=3000):
                    await modal_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            # Seleccionar tipo de documento
            tipo_map = {
                'CC': 'Cédula de Ciudadanía',
                'CE': 'Cédula de Extranjería',
                'TI': 'Tarjeta de Identidad',
                'PA': 'Pasaporte',
                'NIT': 'NIT/RUT',
            }
            
            try:
                select = page.locator('#ctl00_ContentPlaceHolder3_ddlTipoDoc')
                if await select.is_visible(timeout=3000):
                    await select.select_option(label=tipo_map.get(tipo_documento, 'Cédula de Ciudadanía'))
            except Exception:
                pass

            # Ingresar número de documento
            input_doc = page.locator('#ctl00_ContentPlaceHolder3_txtExpediente')
            await input_doc.fill(numero_documento)

            # Click en consultar
            btn_consultar = page.locator('#ctl00_ContentPlaceHolder3_btnConsultar')
            await btn_consultar.click()

            # Esperar resultado
            await page.wait_for_timeout(3000)
            await page.wait_for_load_state('networkidle', timeout=15000)

            # Capturar screenshot del resultado
            filename = f"medidas_{numero_documento}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            await page.screenshot(path=filepath, full_page=True)

            # Intentar detectar el resultado
            content = await page.content()
            content_lower = content.lower()

            if 'no tiene' in content_lower or 'no registra' in content_lower or 'sin medidas' in content_lower:
                estado = 'sin_antecedentes'
                mensaje = 'No registra medidas correctivas'
            elif 'registra' in content_lower and ('medida' in content_lower or 'correctiva' in content_lower):
                estado = 'con_antecedentes'
                mensaje = 'Registra medidas correctivas'
            else:
                estado = 'sin_antecedentes'
                mensaje = 'Consulta completada'

            return {
                "estado": estado,
                "mensaje": mensaje,
                "screenshot_url": f"/outputs/certificados/{filename}"
            }

        except Exception as e:
            return {
                "estado": "error",
                "mensaje": f"Error consultando medidas correctivas: {str(e)[:80]}"
            }
        finally:
            await context.close()

    # ══════════════════════════════════════════════════════════
    # 2. ANTECEDENTES JUDICIALES (Policía Nacional - DIJIN)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    async def _consultar_antecedentes_judiciales(
        browser, tipo_documento: str, numero_documento: str
    ) -> Dict:
        """
        Consulta en: https://antecedentes.policia.gov.co:7005/WebJudicial/
        
        Flujo:
        1. Navegar → aceptar términos de uso
        2. Seleccionar tipo documento
        3. Ingresar número  
        4. Click consultar
        5. Capturar resultado
        """
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            ignore_https_errors=True  # Puerto no estándar puede tener cert issues
        )
        page = await context.new_page()

        try:
            await page.goto(
                'https://antecedentes.policia.gov.co:7005/WebJudicial/',
                wait_until='networkidle',
                timeout=PAGE_TIMEOUT
            )

            # Paso 1: Acuerdo de Términos
            # Aceptar términos haciendo clic en la etiqueta o el radio
            try:
                radio_acepto = page.locator("label[for='aceptaOption:0']")
                if await radio_acepto.is_visible(timeout=5000):
                    await radio_acepto.click()
            except Exception:
                pass

            # Enviar formulario términos
            try:
                btn_continuar = page.locator('#continuarBtn')
                # Esperar a que esté habilitado
                for _ in range(15):
                    if not await btn_continuar.get_attribute('disabled'):
                        break
                    await page.wait_for_timeout(500)
                await btn_continuar.click()
                await page.wait_for_url('**/antecedentes.xhtml', timeout=15000)
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass

            # Paso 2: Formulario de Consulta
            # Seleccionar tipo de documento
            try:
                select = page.locator('#cedulaTipo')
                if await select.is_visible(timeout=5000):
                    tipo_map_judicial = {
                        'CC': 'cc',
                        'CE': 'ce', 
                        'TI': 'ti',
                        'PA': 'pa',
                    }
                    await select.select_option(value=tipo_map_judicial.get(tipo_documento, 'cc'))
            except Exception:
                pass

            # Ingresar número
            try:
                input_doc = page.locator('#cedulaInput')
                await input_doc.fill(numero_documento)
            except Exception:
                pass

            # Click en consultar
            try:
                btn = page.locator('button:has-text("Consultar")')
                await btn.click()
                await page.wait_for_timeout(3000)
                await page.wait_for_load_state('networkidle', timeout=15000)
            except Exception:
                pass

            # Capturar screenshot
            filename = f"judiciales_{numero_documento}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            await page.screenshot(path=filepath, full_page=True)

            # Detectar resultado
            content = await page.content()
            content_lower = content.lower()

            if 'no tiene' in content_lower or 'no registra' in content_lower or 'no aparece' in content_lower:
                estado = 'sin_antecedentes'
                mensaje = 'No registra antecedentes judiciales'
            elif 'registra' in content_lower or 'antecedente' in content_lower:
                estado = 'con_antecedentes'
                mensaje = 'Registra antecedentes judiciales'
            else:
                estado = 'sin_antecedentes'
                mensaje = 'Consulta completada'

            return {
                "estado": estado,
                "mensaje": mensaje,
                "screenshot_url": f"/outputs/certificados/{filename}"
            }

        except Exception as e:
            return {
                "estado": "error",
                "mensaje": f"Error consultando antecedentes judiciales: {str(e)[:80]}"
            }
        finally:
            await context.close()

    # ══════════════════════════════════════════════════════════
    # 3. ANTECEDENTES FISCALES (Contraloría General)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    async def _consultar_antecedentes_fiscales(
        browser, tipo_documento: str, numero_documento: str
    ) -> Dict:
        """
        Consulta en: https://www.contraloria.gov.co/web/guest/persona-natural
        
        Flujo:
        1. Navegar a persona natural
        2. Seleccionar tipo de documento
        3. Ingresar número
        4. Click en generar certificado
        5. Capturar resultado / descargar PDF
        """
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            await page.goto(
                'https://www.contraloria.gov.co/web/guest/persona-natural',
                wait_until='networkidle',
                timeout=PAGE_TIMEOUT
            )

            # Esperar a que cargue el formulario
            await page.wait_for_timeout(3000)

            # Buscar iframe si existe
            frames = page.frames
            target_frame = page
            for frame in frames:
                try:
                    if 'certificado' in (frame.url or '').lower() or 'contraloria' in (frame.url or '').lower():
                        target_frame = frame
                        break
                except Exception:
                    continue

            # Seleccionar tipo de documento
            try:
                tipo_select = target_frame.locator('select').first
                if await tipo_select.is_visible(timeout=5000):
                    tipo_map_fiscal = {
                        'CC': 'C',
                        'CE': 'E',
                        'TI': 'T',
                        'PA': 'P',
                        'NIT': 'N',
                    }
                    await tipo_select.select_option(value=tipo_map_fiscal.get(tipo_documento, 'C'))
            except Exception:
                pass

            # Ingresar número
            try:
                input_doc = target_frame.locator('input[type="text"]').first
                await input_doc.fill(numero_documento)
            except Exception:
                pass

            # Click en generar/consultar
            try:
                btn = target_frame.locator('button:has-text("Generar"), button:has-text("Consultar"), input[type="submit"], input[type="button"]').first
                await btn.click()
                await page.wait_for_timeout(5000)
                await page.wait_for_load_state('networkidle', timeout=15000)
            except Exception:
                pass

            # Capturar screenshot 
            filename = f"fiscales_{numero_documento}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            await page.screenshot(path=filepath, full_page=True)

            # Intentar detectar descarga de PDF
            # La Contraloría puede generar un PDF directamente
            pdf_filename = None
            try:
                # Escuchar por descargas
                async with page.expect_download(timeout=5000) as download_info:
                    pass
                download = await download_info.value
                pdf_filename = f"fiscal_{numero_documento}_{uuid.uuid4().hex[:8]}.pdf"
                pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
                await download.save_as(pdf_path)
            except Exception:
                pdf_filename = None

            # Detectar resultado
            content = await page.content()
            content_lower = content.lower()

            if 'no figura' in content_lower or 'no registra' in content_lower or 'no aparece' in content_lower:
                estado = 'sin_antecedentes'
                mensaje = 'No registra antecedentes fiscales'
            elif 'registra' in content_lower or 'responsabilidad fiscal' in content_lower:
                estado = 'con_antecedentes'
                mensaje = 'Registra antecedentes fiscales'
            else:
                estado = 'sin_antecedentes'
                mensaje = 'Consulta completada'

            result = {
                "estado": estado,
                "mensaje": mensaje,
                "screenshot_url": f"/outputs/certificados/{filename}"
            }

            if pdf_filename:
                result["pdf_url"] = f"/outputs/certificados/{pdf_filename}"

            return result

        except Exception as e:
            return {
                "estado": "error",
                "mensaje": f"Error consultando antecedentes fiscales: {str(e)[:80]}"
            }
        finally:
            await context.close()
