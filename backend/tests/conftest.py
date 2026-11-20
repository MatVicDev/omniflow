import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp(prefix="omniflow-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["AI_PROVIDER"] = "offline"
os.environ["SEED_ON_STARTUP"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def personas(client):
    contacts = client.get("/api/contacts", params={"limit": 200}).json()
    return {c["name"].split()[0].lower(): c for c in contacts}
