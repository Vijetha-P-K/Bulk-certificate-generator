"""Test configuration.

IMPORTANT: environment variables are set *before* any `app.*` import so that
`app.config` and `app.database` pick up the test values.
"""
import os
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.mkdtemp(prefix="bcg-tests-"))

os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DIR / 'test.db'}"
os.environ["CERT_OUTPUT_DIR"] = str(_TMP_DIR / "generated")
os.environ["CERT_PROCESSING_MODE"] = "inline"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_db():
    """Give every test a clean database so IDs are predictable."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client(_reset_db):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_payload():
    return {
        "event_name": "Python Workshop",
        "date": "2026-10-10",
        "recipients": [
            {"name": "Arun Kumar", "email": "arun@example.com"},
            {"name": "Priya Kumar", "email": "priya@example.com"},
        ],
    }