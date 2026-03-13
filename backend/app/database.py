"""
Database - Conexión a PostgreSQL con SQLAlchemy
================================================

Configuración de la conexión a la base de datos PostgreSQL.
Incluye:
- Engine asíncrono con pool de conexiones
- Session factory
- Base declarativa para modelos
- Función de inicialización (crear tablas + admin seed)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CONEXIÓN
# ══════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://consolidador_admin:C0ns0l1d4d0r_S3cur3_2025!@localhost:5432/consolidador_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    echo=os.getenv("DEBUG", "False").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ══════════════════════════════════════════════════════════════
# DEPENDENCY INJECTION (FastAPI)
# ══════════════════════════════════════════════════════════════

def get_db():
    """Generador de sesiones para inyección en endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
# INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════

def init_db():
    """Crea todas las tablas y el usuario admin por defecto."""
    from app.models.user import User  # Import aquí para evitar circular
    
    Base.metadata.create_all(bind=engine)
    
    # Crear admin por defecto si no existe
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            from app.services.auth_service import AuthService
            hashed = AuthService.hash_password("Admin@Gestar2025!")
            admin_user = User(
                username="admin",
                email="admin@gestar.com",
                hashed_password=hashed,
                full_name="Administrador",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Usuario admin creado: admin / Admin@Gestar2025!")
        else:
            print("ℹ️ Usuario admin ya existe")
    except Exception as e:
        print(f"⚠️ Error creando admin: {e}")
        db.rollback()
    finally:
        db.close()
