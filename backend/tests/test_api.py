from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404():
    response = client.get("/khong-ton-tai")

    assert response.status_code == 404


def test_routes_live_under_api_prefix_only():
    assert client.get("/health").status_code == 404
    assert client.get("/reception/doctors").status_code == 404


def test_openapi_and_docs_are_served_under_api_prefix():
    schema = client.get("/api/openapi.json")

    assert schema.status_code == 200
    assert "/api/reception/appointments" in schema.json()["paths"]
    assert client.get("/api/docs").status_code == 200
