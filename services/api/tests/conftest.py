"""Pytest fixtures for the OpsBrain API test suite.

Points the app at an isolated SQLite file (never the dev opsbrain.db) and
seeds it once per test session so endpoint tests exercise the real
ingestion + reasoning pipeline end-to-end, not mocks.
"""
from __future__ import annotations

import os
import sys

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_opsbrain.db")

# Must happen BEFORE importing anything from `app` (db.py reads
# DATABASE_URL at import time to decide which engine to build).
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# Force the fully-offline/deterministic path for tests regardless of any local
# .env with a real GEMINI_API_KEY — keeps the suite fast, hermetic, and free of
# network calls. (config.gemini_api_key() honours this flag first.)
os.environ["OPSBRAIN_DISABLE_GEMINI"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import run_seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    init_db()
    db = SessionLocal()
    run_seed(db)
    db.close()
    yield


@pytest.fixture(scope="session")
def client(_seeded_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db_session(_seeded_db):
    session = SessionLocal()
    yield session
    session.close()
