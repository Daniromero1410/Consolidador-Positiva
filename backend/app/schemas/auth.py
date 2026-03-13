"""
Auth Schemas - Esquemas Pydantic para autenticación
=====================================================

Validación de datos de entrada/salida para los endpoints de auth.
Incluye validación de contraseñas seguras y sanitización de inputs.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


# ══════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    """Schema para login."""
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v):
        """Sanitizar username para prevenir inyección."""
        v = v.strip()
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Username solo puede contener letras, números, puntos, guiones y guiones bajos')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username debe tener entre 3 y 50 caracteres')
        return v


class CreateUserRequest(BaseModel):
    """Schema para crear usuario (solo admin)."""
    username: str
    email: str
    password: str
    full_name: str
    role: str = "analyst"

    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v):
        v = v.strip()
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Username solo puede contener letras, números, puntos, guiones y guiones bajos')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username debe tener entre 3 y 50 caracteres')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email inválido')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validar contraseña segura."""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ('admin', 'analyst', 'projects'):
            raise ValueError('Rol debe ser "admin", "analyst", o "projects"')
        return v

    @field_validator('full_name')
    @classmethod
    def sanitize_full_name(cls, v):
        """Sanitizar nombre para prevenir XSS."""
        v = v.strip()
        v = re.sub(r'[<>"\'/;(){}]', '', v)
        if len(v) < 2 or len(v) > 100:
            raise ValueError('Nombre debe tener entre 2 y 100 caracteres')
        return v


class UpdateUserRequest(BaseModel):
    """Schema para actualizar usuario."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in ('admin', 'analyst', 'projects'):
            raise ValueError('Rol debe ser "admin", "analyst", o "projects"')
        return v


# ══════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ══════════════════════════════════════════════════════════════

class TokenResponse(BaseModel):
    """Schema de respuesta con tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """Schema de respuesta de usuario (sin contraseña)."""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Schema para refresh token."""
    refresh_token: str
