"""
Auth Service - Servicio de autenticación
==========================================

Lógica de negocio para autenticación:
- Hash de contraseñas con bcrypt
- Generación y validación de JWT tokens
- Rate limiting por IP
- Bloqueo de cuentas por intentos fallidos
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from collections import defaultdict

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN JWT
# ══════════════════════════════════════════════════════════════

JWT_SECRET = os.getenv("JWT_SECRET", "g3st4r_c0ns0l1d4d0r_s3cr3t_k3y_2025_pr0duct10n!")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ══════════════════════════════════════════════════════════════
# SEGURIDAD: CONFIGURACIÓN ANTI-BRUTE-FORCE
# ══════════════════════════════════════════════════════════════

MAX_FAILED_ATTEMPTS = 5          # Intentos antes de bloquear cuenta
ACCOUNT_LOCK_MINUTES = 15        # Duración del bloqueo
RATE_LIMIT_WINDOW = 60           # Ventana de rate limit (segundos)
RATE_LIMIT_MAX_REQUESTS = 10     # Máx requests por ventana por IP


class AuthService:
    """Servicio de autenticación con protecciones de seguridad."""

    # Rate limiting en memoria (por IP)
    _rate_limits: Dict[str, list] = defaultdict(list)

    # ══════════════════════════════════════════════════════════
    # CONTRASEÑAS (bcrypt)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de contraseña con bcrypt + salt automático."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica contraseña contra hash bcrypt."""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════
    # JWT TOKENS
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def create_access_token(user_id: int, username: str, role: str) -> str:
        """Crea un access token JWT."""
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Crea un refresh token JWT (larga duración)."""
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verifica y decodifica un JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # ══════════════════════════════════════════════════════════
    # RATE LIMITING
    # ══════════════════════════════════════════════════════════

    @classmethod
    def check_rate_limit(cls, client_ip: str) -> Tuple[bool, int]:
        """
        Verifica rate limit por IP.
        
        Returns:
            (allowed: bool, remaining: int)
        """
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW

        # Limpiar requests antiguos
        cls._rate_limits[client_ip] = [
            t for t in cls._rate_limits[client_ip]
            if t > window_start
        ]

        current_count = len(cls._rate_limits[client_ip])

        if current_count >= RATE_LIMIT_MAX_REQUESTS:
            return False, 0

        cls._rate_limits[client_ip].append(now)
        return True, RATE_LIMIT_MAX_REQUESTS - current_count - 1

    # ══════════════════════════════════════════════════════════
    # BLOQUEO DE CUENTAS
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def is_account_locked(locked_until: Optional[datetime]) -> bool:
        """Verifica si una cuenta está bloqueada."""
        if locked_until is None:
            return False
        return datetime.utcnow() < locked_until

    @staticmethod
    def get_lock_until() -> datetime:
        """Obtiene la fecha/hora hasta la cual bloquear la cuenta."""
        return datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCK_MINUTES)

    @staticmethod
    def should_lock_account(failed_attempts: int) -> bool:
        """Determina si se debe bloquear la cuenta."""
        return failed_attempts >= MAX_FAILED_ATTEMPTS
