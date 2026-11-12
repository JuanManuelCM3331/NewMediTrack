"""Migra esquema (vía Alembic) y datos existentes desde SQLite (meditrack.db) hacia MySQL."""
import argparse
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import settings
from core.database import Base, build_engine_kwargs, ensure_mysql_database_exists
import models  # noqa: F401 - Registra todos los modelos en Base.metadata


def run_alembic_upgrade(mysql_url: str) -> None:
    """Aplica todas las migraciones de Alembic sobre la base MySQL destino."""
    alembic_cfg = Config(str(ROOT_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", mysql_url)
    command.upgrade(alembic_cfg, "head")


def normalize_mysql_url(raw_url: str) -> str:
    if raw_url.startswith("mysql://"):
        return "mysql+pymysql://" + raw_url[len("mysql://"):]
    return raw_url


def migrate_sqlite_to_mysql(sqlite_path: Path, mysql_url: str, replace: bool = False) -> dict[str, tuple[int, int]]:
    """Copia todas las tablas y registros de SQLite hacia MySQL conservando IDs y AUTO_INCREMENT."""
    if not sqlite_path.exists():
        raise FileNotFoundError(f"No se encontró la base SQLite origen: {sqlite_path}")

    target_url = normalize_mysql_url(mysql_url)
    if not target_url.startswith("mysql"):
        raise ValueError(f"La URL destino debe ser MySQL: {target_url}")

    ensure_mysql_database_exists(target_url)
    run_alembic_upgrade(target_url)

    sqlite_url = f"sqlite:///{sqlite_path.resolve().as_posix()}"
    sqlite_engine = create_engine(sqlite_url, **build_engine_kwargs(sqlite_url))
    mysql_engine = create_engine(target_url, **build_engine_kwargs(target_url))

    tables = list(Base.metadata.sorted_tables)
    summary: dict[str, tuple[int, int]] = {}

    try:
        with mysql_engine.connect() as mysql_conn:
            non_empty = []
            for table in tables:
                count = mysql_conn.scalar(select(func.count()).select_from(table)) or 0
                if count > 0:
                    non_empty.append(f"{table.name} ({count})")

            if non_empty and not replace:
                raise RuntimeError(
                    "La base de datos MySQL destino ya contiene datos en: "
                    + ", ".join(non_empty)
                    + ". Usa --replace para reemplazar los registros existentes."
                )

        with sqlite_engine.connect() as sqlite_conn, mysql_engine.begin() as mysql_conn:
            if replace:
                mysql_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                for table in reversed(tables):
                    mysql_conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
                mysql_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

            for table in tables:
                rows = [dict(row._mapping) for row in sqlite_conn.execute(select(table)).fetchall()]
                if rows:
                    mysql_conn.execute(table.insert(), rows)
                    max_id = max(row["id"] for row in rows if "id" in row and row["id"] is not None)
                    mysql_conn.execute(text(f"ALTER TABLE `{table.name}` AUTO_INCREMENT = {int(max_id) + 1}"))

                mysql_count = mysql_conn.scalar(select(func.count()).select_from(table)) or 0
                summary[table.name] = (len(rows), mysql_count)
    finally:
        sqlite_engine.dispose()
        mysql_engine.dispose()

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra MediTrack de SQLite a MySQL.")
    parser.add_argument(
        "--sqlite-path",
        default=str(ROOT_DIR / "meditrack.db"),
        help="Ruta al archivo SQLite origen (por defecto: meditrack.db)",
    )
    parser.add_argument(
        "--mysql-url",
        default=settings.database_url,
        help="URL SQLAlchemy de destino MySQL (por defecto: DATABASE_URL configurada en .env)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Trunca las tablas destino en MySQL antes de copiar los datos de SQLite",
    )
    args = parser.parse_args()

    summary = migrate_sqlite_to_mysql(
        sqlite_path=Path(args.sqlite_path),
        mysql_url=args.mysql_url,
        replace=args.replace,
    )

    print("Migración de SQLite a MySQL completada:")
    for table_name, (src_count, dst_count) in summary.items():
        print(f"  - {table_name}: SQLite={src_count} -> MySQL={dst_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
