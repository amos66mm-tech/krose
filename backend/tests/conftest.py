from __future__ import annotations

import os
import tempfile

import pytest


def pytest_configure() -> None:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    os.environ["ENABLE_SCHEDULER"] = "false"
    os.environ["ALLOW_MOCK_FALLBACK"] = "true"
    os.environ["EXA_API_KEY"] = ""
    os.environ["LLM_API_KEY"] = ""
    os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")


@pytest.fixture(scope="session")
def seeded_db():
    from app.config import get_settings

    get_settings.cache_clear()
    from app.database import SessionLocal, configure_database, init_db
    from app.seed import run_seed

    configure_database(os.environ["DATABASE_URL"])
    init_db()
    db = SessionLocal()
    run_seed(db)
    yield db
    db.close()


@pytest.fixture(scope="session")
def client(seeded_db):  # noqa: ARG001
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
