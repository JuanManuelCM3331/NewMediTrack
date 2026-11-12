from collections.abc import Generator
import logging
import re

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, declared_attr, sessionmaker

from core.config import settings

logger = logging.getLogger("meditrack.database")

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def build_engine_kwargs(database_url: str) -> dict:
    """Construye los argumentos de SQLAlchemy adecuados según el motor de base de datos."""
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    kwargs: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 10,
        "max_overflow": 20,
    }
    if database_url.startswith("mysql+pymysql"):
        kwargs["connect_args"] = {"charset": "utf8mb4"}
    return kwargs


is_sqlite = settings.database_url.startswith("sqlite")
engine = create_engine(settings.database_url, **build_engine_kwargs(settings.database_url))

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    @declared_attr.directive
    @classmethod
    def __table_args__(cls) -> dict:
        return dict(MYSQL_TABLE_ARGS)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_mysql_database_exists(database_url: str) -> None:
    """Crea la base de datos MySQL en charset utf8mb4 si aún no existe."""
    url = make_url(database_url)
    if not url.drivername.startswith("mysql") or not url.database:
        return
    if not re.fullmatch(r"[A-Za-z0-9_$-]+", url.database):
        raise ValueError(f"Nombre de base de datos MySQL inválido: {url.database}")

    server_url = url.set(database="")
    temp_engine = create_engine(server_url, isolation_level="AUTOCOMMIT", **build_engine_kwargs(database_url))
    try:
        with temp_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        temp_engine.dispose()


def init_db():
    """Inicializa tablas y aplica migraciones ligeras automáticas de esquema si es necesario."""
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as err:
        orig_args = getattr(err.orig, "args", ())
        if settings.is_development and 1049 in orig_args and settings.database_url.startswith("mysql"):
            logger.info("Base de datos MySQL no encontrada en desarrollo; creándola automáticamente...")
            ensure_mysql_database_exists(settings.database_url)
            Base.metadata.create_all(bind=engine)
        else:
            raise

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
