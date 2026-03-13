"""
Auth API - Endpoints de autenticación
=======================================

Endpoints para:
- POST /auth/login         → Login con username/password
- POST /auth/refresh       → Renovar access token
- POST /auth/users         → Crear usuario (solo admin)
- GET  /auth/users         → Listar usuarios (solo admin)
- GET  /auth/users/me      → Info del usuario actual
- PUT  /auth/users/{id}    → Actualizar usuario (solo admin)
- DELETE /auth/users/{id}  → Desactivar usuario (solo admin)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, CreateUserRequest, UpdateUserRequest,
    TokenResponse, UserResponse, RefreshTokenRequest
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ══════════════════════════════════════════════════════════════
# HELPER: Obtener usuario actual desde JWT
# ══════════════════════════════════════════════════════════════

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extrae y valida el usuario del token JWT en el header Authorization."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth_header.split(" ")[1]
    payload = AuthService.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido"
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Requiere que el usuario sea admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Login con username y password.
    
    Protecciones:
    - Rate limiting por IP (máx 10 requests/min)
    - Bloqueo de cuenta tras 5 intentos fallidos (15 min)
    - Timing-safe password comparison (bcrypt)
    """
    # 1. Rate limiting por IP
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = AuthService.check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Espere un momento antes de reintentar.",
            headers={"Retry-After": "60"}
        )

    # 2. Buscar usuario
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # 3. Verificar si la cuenta está bloqueada
    if AuthService.is_account_locked(user.locked_until):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Cuenta bloqueada por demasiados intentos fallidos. Intente después de {user.locked_until.strftime('%H:%M:%S')}"
        )

    # 4. Verificar contraseña
    if not AuthService.verify_password(data.password, user.hashed_password):
        # Incrementar intentos fallidos
        user.failed_login_attempts += 1
        
        if AuthService.should_lock_account(user.failed_login_attempts):
            user.locked_until = AuthService.get_lock_until()
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Cuenta bloqueada por {user.failed_login_attempts} intentos fallidos. Desbloqueada en 15 minutos."
            )
        
        db.commit()
        remaining_attempts = 5 - user.failed_login_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Credenciales incorrectas. {remaining_attempts} intento(s) restante(s)."
        )

    # 5. Verificar cuenta activa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada. Contacte al administrador."
        )

    # 6. Login exitoso - resetear intentos
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()

    # 7. Generar tokens
    access_token = AuthService.create_access_token(user.id, user.username, user.role)
    refresh_token = AuthService.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,  # 30 minutos en segundos
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Renueva el access token usando un refresh token válido."""
    payload = AuthService.verify_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    access_token = AuthService.create_access_token(user.id, user.username, user.role)
    new_refresh = AuthService.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=30 * 60,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    )


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Obtiene la información del usuario actual."""
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios (solo admin)."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: CreateUserRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario (solo admin)."""
    # Verificar duplicados
    existing = db.query(User).filter(
        (User.username == data.username) | (User.email == data.email)
    ).first()
    
    if existing:
        if existing.username == data.username:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=AuthService.hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Actualiza un usuario (solo admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.email is not None:
        user.email = data.email
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.hashed_password = AuthService.hash_password(data.password)
        user.failed_login_attempts = 0
        user.locked_until = None

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Desactiva un usuario (solo admin). No elimina el registro."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No puede desactivar su propia cuenta")

    user.is_active = False
    db.commit()

    return {"message": f"Usuario '{user.username}' desactivado exitosamente"}
