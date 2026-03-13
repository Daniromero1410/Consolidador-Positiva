"""
Consolidador T25 - API Principal
================================

API FastAPI para el sistema de consolidación de tarifas POSITIVA.
Incluye:
- Sistema de autenticación JWT (PostgreSQL)
- Módulo Consolidador T25 (protegido)
- Módulo Descarga de Certificados (público)
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import os
import time
import sys
import asyncio

# Corrección para el error 'NotImplementedError' de Subprocess (Playwright) en Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.api import upload, sftp, process, download, auth, certificados
from app.websockets import logs
from app.database import init_db


# ══════════════════════════════════════════════════════════════
# MIDDLEWARE DE SEGURIDAD
# ══════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega headers de seguridad a todas las respuestas."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevenir MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevenir XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        return response


# ══════════════════════════════════════════════════════════════
# CREAR APLICACIÓN
# ══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Consolidador T25 API",
    description="API para consolidación de tarifas POSITIVA + Descarga de Certificados",
    version="16.0.0"
)

# Middleware de seguridad
app.add_middleware(SecurityHeadersMiddleware)

# Configurar CORS
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear carpetas si no existen
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Montar carpeta de archivos estáticos (para descargas)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


# ══════════════════════════════════════════════════════════════
# REGISTRAR ROUTERS
# ══════════════════════════════════════════════════════════════

# 🔓 Auth (público)
app.include_router(auth.router, prefix="/api", tags=["Autenticación"])

# 🔒 Consolidador T25 (protegido por JWT en cada endpoint)
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(sftp.router, prefix="/api", tags=["SFTP"])
app.include_router(process.router, prefix="/api", tags=["Process"])
app.include_router(download.router, prefix="/api", tags=["Download"])

# 🌐 Certificados (público)
app.include_router(certificados.router, prefix="/api", tags=["Certificados"])

# WebSocket
app.include_router(logs.router, tags=["WebSocket"])


# ══════════════════════════════════════════════════════════════
# EVENTOS DE STARTUP
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos y crear admin al arrancar."""
    print("🚀 Inicializando base de datos...")
    init_db()
    print("✅ Base de datos inicializada")


# ══════════════════════════════════════════════════════════════
# ENDPOINTS BASE
# ══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Endpoint raíz - información de la API."""
    return {
        "message": "Consolidador T25 + Certificados API",
        "version": "16.0.0",
        "status": "running",
        "docs": "/docs",
        "modules": {
            "consolidador_t25": {
                "description": "Consolidación de tarifas (requiere autenticación)",
                "endpoints": {
                    "upload": "/api/upload/maestra",
                    "sftp": "/api/sftp/conectar",
                    "process": "/api/procesar",
                    "download": "/api/descargas/listar"
                }
            },
            "autenticacion": {
                "description": "Sistema de autenticación JWT",
                "endpoints": {
                    "login": "/api/auth/login",
                    "refresh": "/api/auth/refresh",
                    "users": "/api/auth/users"
                }
            }
        }
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "version": "16.0.0"}


@app.get("/api/info")
async def api_info():
    """Información detallada de la API."""
    return {
        "nombre": "Consolidador T25 + Certificados",
        "version": "16.0.0",
        "descripcion": "Sistema de consolidación de tarifas y descarga de certificados",
        "modulos": [
            {
                "nombre": "Consolidador T25",
                "descripcion": "Consolidación automática de tarifas de prestadores de salud",
                "requiere_auth": True
            },
            {
                "nombre": "Descarga de Certificados",
                "descripcion": "Descarga automatizada de certificados gubernamentales",
                "requiere_auth": False
            }
        ]
    }

