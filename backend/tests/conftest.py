import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests that consume Claude API credits"
    )


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test that consumes API credits (deselect with '-m \"not e2e\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless --run-e2e flag is provided"""
    if config.getoption("--run-e2e"):
        # E2E tests should run
        return

    skip_e2e = pytest.mark.skip(reason="Need --run-e2e option to run E2E tests")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()