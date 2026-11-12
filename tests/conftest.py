import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import close_all_sessions, sessionmaker
from sqlalchemy.pool import NullPool

os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "development"

TEST_DB_FILE = "./test_temp.db"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{TEST_DB_FILE}")
IS_TEST_SQLITE = TEST_DATABASE_URL.startswith("sqlite")

from core.database import Base, build_engine_kwargs, ensure_mysql_database_exists, get_db

if TEST_DATABASE_URL.startswith("mysql"):
    ensure_mysql_database_exists(TEST_DATABASE_URL)

engine_kwargs = build_engine_kwargs(TEST_DATABASE_URL)
if IS_TEST_SQLITE:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs = {
        k: v for k, v in engine_kwargs.items() if k not in {"pool_size", "max_overflow"}
    }
    engine_kwargs["poolclass"] = NullPool

TEST_ENGINE = create_engine(TEST_DATABASE_URL, **engine_kwargs)

if IS_TEST_SQLITE:
    @event.listens_for(TEST_ENGINE, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False, expire_on_commit=False)

from core.rate_limiter import limiter
from main import app


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def db_session():
    close_all_sessions()
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    limiter.enabled = False
    yield
    close_all_sessions()
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client():
    return TestClient(app)


def pytest_sessionfinish(session, exitstatus):
    """Limpia la base de datos temporal al terminar las pruebas."""
    try:
        TEST_ENGINE.dispose()
        if IS_TEST_SQLITE and os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
    except Exception:
        pass
