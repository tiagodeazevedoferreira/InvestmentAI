from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_api_health_exposes_request_id_and_security_headers():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    UUID(response.headers["X-Request-ID"])
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_api_preserves_valid_request_id():
    request_id = "12345678-1234-5678-1234-567812345678"

    response = client.get("/api/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_api_replaces_invalid_request_id():
    response = client.get("/api/health", headers={"X-Request-ID": "not-a-uuid"})

    assert response.status_code == 200
    UUID(response.headers["X-Request-ID"])
    assert response.headers["X-Request-ID"] != "not-a-uuid"
\n\ndef test_api_readiness_is_ready_by_default():
    response = client.get("/api/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["trading_mode"] == "simulation"


def test_api_readiness_fails_closed_for_unsafe_live_configuration(monkeypatch):
    from app.api import routes

    monkeypatch.setattr(routes.settings, "trading_mode", routes.TradingMode.LIVE)
    monkeypatch.setattr(routes.settings, "live_trading_enabled", False)
    monkeypatch.setattr(routes.settings, "model_approved", False)
    monkeypatch.setattr(routes.settings, "risk_gate_enabled", False)

    response = client.get("/api/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert "live trading is disabled" in response.json()["issues"]
    assert "live model approval is missing" in response.json()["issues"]
    assert "risk gate is disabled" in response.json()["issues"]
