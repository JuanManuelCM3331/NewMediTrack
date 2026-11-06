"""Fachada de base de datos para compatibilidad retroactiva.
Delega a core.database.
"""

from core.database import Base, SessionLocal, engine, get_db, init_db

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db"]
