import pytest
from fastapi.testclient import TestClient

from app.config import CorsSettings
from app.main import create_app


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    # Tránh đọc nhầm file .env thật trong thư mục chạy test.
    monkeypatch.chdir(tmp_path)


def _preflight(client: TestClient, origin: str, path: str = "/reception/doctors"):
    return client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )


def test_cors_settings_default_is_empty(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)

    assert CorsSettings().origins() == []


def test_cors_settings_parses_comma_separated_origins_and_trims_blanks(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", " http://a.test , ,http://b.test,")

    assert CorsSettings().origins() == ["http://a.test", "http://b.test"]


def test_cors_disabled_by_default_returns_no_allow_origin_header(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "null"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_wildcard_allows_opaque_origin_on_simple_request(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "null"})

    assert response.headers["access-control-allow-origin"] == "*"


def test_cors_wildcard_preflight_allows_authorization_header(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    client = TestClient(create_app())

    response = _preflight(client, "null")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_cors_does_not_allow_credentials(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    client = TestClient(create_app())

    response = _preflight(client, "null")

    assert "access-control-allow-credentials" not in response.headers


def test_cors_listed_origin_is_allowed(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://allowed.test")
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://allowed.test"})

    assert response.headers["access-control-allow-origin"] == "http://allowed.test"


def test_cors_unlisted_origin_is_not_allowed(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://allowed.test")
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://evil.test"})

    assert "access-control-allow-origin" not in response.headers


def test_cors_headers_present_on_unauthorized_response(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    client = TestClient(create_app())

    response = client.get("/reception/doctors", headers={"Origin": "null"})

    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == "*"
