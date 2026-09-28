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
