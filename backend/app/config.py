"""
Configuración centralizada del Consolidador T25
"""

import os
from dataclasses import dataclass, field
from typing import Set
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


@dataclass
class Config:
    """Configuración centralizada del sistema."""
    
    # SFTP
    HOST: str = os.getenv('SFTP_HOST', 'mft.positiva.gov.co')
    PORT: int = int(os.getenv('SFTP_PORT', 2243))
    USERNAME: str = os.getenv('SFTP_USERNAME', '')
    PASSWORD: str = os.getenv('SFTP_PASSWORD', '')
    
    # Timeouts
    TIMEOUT_CONEXION: int = int(os.getenv('TIMEOUT_CONEXION', 30))
    TIMEOUT_OPERACION: int = int(os.getenv('TIMEOUT_OPERACION', 20))
    TIMEOUT_ARCHIVO: int = int(os.getenv('TIMEOUT_ARCHIVO', 60))
    
    # Reintentos
    MAX_REINTENTOS_CONEXION: int = int(os.getenv('MAX_REINTENTOS_CONEXION', 5))
    MAX_REINTENTOS_OPERACION: int = int(os.getenv('MAX_REINTENTOS_OPERACION', 3))
    BACKOFF_BASE: float = float(os.getenv('BACKOFF_BASE', 2.0))
    KEEPALIVE_INTERVAL: int = int(os.getenv('KEEPALIVE_INTERVAL', 5))
    
    # Carpetas
    CARPETA_PRINCIPAL: str = os.getenv('CARPETA_PRINCIPAL', 'R.A-ABASTECIMIENTO RED ASISTENCIAL')
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER: str = os.getenv('OUTPUT_FOLDER', 'outputs')
    
    # Otros
    MAX_SEDES: int = int(os.getenv('MAX_SEDES', 50))
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    CONTRATOS_PROBLEMATICOS: Set[str] = field(default_factory=lambda: {'572-2023'})
    TIMEOUT_CONTRATOS_PROBLEMATICOS: int = 30


# Instancia global de configuración
CONFIG = Config()
