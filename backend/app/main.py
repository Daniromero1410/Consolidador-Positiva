"""
Consolidador T25 - API Principal
================================

API FastAPI para el sistema de consolidación de tarifas POSITIVA.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import upload, sftp, process, download
from app.websockets import logs

# Crear aplicación FastAPI
app = FastAPI(
    title="Consolidador T25 API",
    description="API para el sistema de consolidación de tarifas POSITIVA",
    version="15.1.0"
)

# Configurar CORS para permitir conexiones desde el frontend
# Obtener orígenes permitidos desde variable de entorno o usar "*" por defecto
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

# Registrar routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(sftp.router, prefix="/api", tags=["SFTP"])
app.include_router(process.router, prefix="/api", tags=["Process"])
app.include_router(download.router, prefix="/api", tags=["Download"])

# Registrar WebSocket
app.include_router(logs.router, tags=["WebSocket"])


@app.get("/")
async def root():
    """Endpoint raíz - información de la API."""
    return {
        "message": "Consolidador T25 API",
        "version": "15.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "upload": "/api/upload/maestra",
            "sftp": "/api/sftp/conectar",
            "process": "/api/procesar",
            "download": "/api/descargas/listar"
        }
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy"}


@app.get("/api/info")
async def api_info():
    """Información detallada de la API."""
    return {
        "nombre": "Consolidador T25",
        "version": "15.1.0",
        "descripcion": "Sistema de consolidación de tarifas de prestadores de salud",
        "funcionalidades": [
            "Carga y análisis de maestra de contratos",
            "Conexión SFTP a GoAnywhere",
            "Procesamiento automático de anexos de tarifas",
            "Validación de CUPS y detección de anomalías",
            "ETL con Machine Learning",
            "Generación de reportes consolidados"
        ]
    }
