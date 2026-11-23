import pytest

pytest.importorskip("fastapi")
pytest.importorskip("slowapi")
pytest.importorskip("langchain_google_genai")

from fastapi.testclient import TestClient  # noqa: E402

from pfefinder.api.main import app  # noqa: E402


def test_health():
    assert TestClient(app).get("/api/health").json() == {"status": "ok"}
