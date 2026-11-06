import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "development"

TEST_DB_FILE = "./test_temp.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

TEST_ENGINE = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False, expire_on_commit=False)

from database import Base, get_db
from main import app
from rate_limiter import limiter


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    limiter.enabled = False
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client():
    return TestClient(app)


def pytest_sessionfinish(session, exitstatus):
    """Limpia el archivo de base de datos temporal al terminar las pruebas."""
    try:
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
    except Exception:
        pass
