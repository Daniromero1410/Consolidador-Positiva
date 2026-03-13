"""
Certificados API - Endpoints para descarga de certificados
=============================================================

Endpoints públicos (no requieren autenticación):
- POST /certificados/consultar  → Consulta certificados gubernamentales
- GET  /certificados/estado     → Estado del servicio Playwright
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List
import re

from app.services.certificados_service import CertificadosService

router = APIRouter(prefix="/certificados", tags=["Certificados"])


# ══════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════

class ConsultarRequest(BaseModel):
    """Schema para consulta de certificados."""
    tipo_documento: str
    numero_documento: str
    certificados: List[str]

    @field_validator('tipo_documento')
    @classmethod
    def validate_tipo(cls, v):
        valid = ['CC', 'CE', 'TI', 'PA', 'NIT']
        if v not in valid:
            raise ValueError(f'Tipo de documento debe ser uno de: {", ".join(valid)}')
        return v

    @field_validator('numero_documento')
    @classmethod
    def validate_numero(cls, v):
        v = v.strip()
        if not re.match(r'^[0-9]{5,15}$', v):
            raise ValueError('Número de documento debe tener entre 5 y 15 dígitos')
        return v

    @field_validator('certificados')
    @classmethod
    def validate_certificados(cls, v):
        valid = ['medidas', 'disciplinarios', 'fiscales']
        for cert in v:
            if cert not in valid:
                raise ValueError(f'Certificado inválido: {cert}. Válidos: {", ".join(valid)}')
        if len(v) == 0:
            raise ValueError('Debe seleccionar al menos un certificado')
        return v


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.post("/consultar")
async def consultar_certificados(data: ConsultarRequest):
    """
    Consulta certificados gubernamentales usando Playwright.
    
    Este endpoint es PÚBLICO (no requiere autenticación).
    
    - **tipo_documento**: CC, CE, TI, PA, NIT
    - **numero_documento**: Número del documento (5-15 dígitos)
    - **certificados**: Lista de certificados a consultar
    
    Returns:
        Dict con resultado de cada certificado consultado
    """
    try:
        resultados = await CertificadosService.consultar(
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            certificados=data.certificados
        )
        return resultados
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar certificados: {str(e)[:100]}"
        )


def _check_playwright_sync():
    """Ejecuta un check de Playwright en un nuevo Event Loop (Windows compatible)."""
    import sys
    import asyncio
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _internal_check():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            
    try:
        loop.run_until_complete(_internal_check())
    finally:
        loop.close()

@router.get("/estado")
async def estado_servicio():
    """Verifica si Playwright está disponible."""
    import asyncio
    try:
        await asyncio.to_thread(_check_playwright_sync)
        return {
            "disponible": True,
            "mensaje": "Playwright configurado correctamente y soportado en Windows"
        }
    except Exception as e:
        return {
            "disponible": False,
            "mensaje": f"Playwright no disponible: {str(e)[:100]}"
        }
