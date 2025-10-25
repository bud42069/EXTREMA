from app.main import app
from fastapi.testclient import TestClient


def test_health():
    c = TestClient(app)
    r = c.get("/api/health/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"