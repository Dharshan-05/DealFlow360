from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "DealFlow360 API Foundation Operational" in data["message"]
    assert "G01" in data["phase"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DealFlow360"
    assert data["version"] == "0.1.0"
    assert "G01" in data["phase"]
