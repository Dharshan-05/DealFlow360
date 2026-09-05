from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "DealFlow360 API Foundation Operational" in data["message"]
    assert "/docs" in data["docs_url"]
    assert "/api/v1/health" in data["v1_health"]


def test_legacy_health_backward_compatibility():
    """Verify G01 GET /health remains functional and backward-compatible."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DealFlow360"
    assert data["version"] == "0.1.0"


def test_v1_health():
    """Verify G02 GET /api/v1/health versioned router endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "DealFlow360 API v1 operational"
    assert body["data"]["status"] == "healthy"
    assert body["data"]["service"] == "DealFlow360"
    assert "G03" in body["data"]["phase"]
    assert "database" in body["data"]
    assert body["data"]["database"]["connected"] is True
    assert body["data"]["database"]["dialect"] == "postgresql"


def test_openapi_docs_available():
    """Verify OpenAPI JSON and documentation endpoints are served."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert schema["info"]["title"] == "DealFlow360"
    assert "/api/v1/health" in schema["paths"]
    assert "/health" in schema["paths"]
