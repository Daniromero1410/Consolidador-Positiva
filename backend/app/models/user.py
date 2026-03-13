"""
User Model - Modelo de usuario para autenticación
==================================================

Modelo SQLAlchemy para la tabla de usuarios.
Incluye campos de seguridad: hash de contraseña, intentos fallidos,
bloqueo de cuenta, y timestamps de auditoría.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class User(Base):
    """Modelo de usuario con seguridad reforzada."""
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    
    # Roles: 'admin' | 'analyst' | 'projects'
    role = Column(String(20), nullable=False, default="analyst")
    
    # Estado de la cuenta
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Seguridad: protección contra fuerza bruta
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
