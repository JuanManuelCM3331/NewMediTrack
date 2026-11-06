from collections.abc import Generator
import logging

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings

logger = logging.getLogger("meditrack.database")

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(settings.database_url, connect_args=connect_args)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa tablas y aplica migraciones ligeras automáticas de esquema si es necesario."""
    Base.metadata.create_all(bind=engine)
    try:
        insp = inspect(engine)
        if "doses" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("doses")]
            if "created_at" not in cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE doses ADD COLUMN created_at DATETIME"))
                    conn.commit()
    except Exception as err:
        logger.warning("Error al verificar migración de columnas: %s", err)
