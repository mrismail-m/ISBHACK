from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_unbuilt_endpoint_returns_501_error_envelope() -> None:
    res = client.get("/api/v1/evaluation/trust-report")
    assert res.status_code == 501
    assert res.json() == {"error": {"code": "not_implemented", "message": "Not implemented yet (owner: Adeel)."}}
