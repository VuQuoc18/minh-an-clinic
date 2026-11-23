import pytest

from app.core import security

ENDPOINTS = [
    ("get", "/api/reception/appointments"),
    ("post", "/api/reception/appointments/1/check-in"),
    ("get", "/api/reception/specialties"),
    ("get", "/api/reception/doctors"),
    ("get", "/api/reception/walk-in/suggestions?specialty_id=1"),
    ("get", "/api/reception/profiles?phone=0912345678"),
    ("post", "/api/reception/walk-in"),
]


@pytest.mark.parametrize(("method", "url"), ENDPOINTS)
def test_without_token_returns_401(client, method, url):
    response = getattr(client, method)(url)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize(("method", "url"), ENDPOINTS)
def test_unknown_token_returns_401(client, method, url):
    response = getattr(client, method)(url, headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_TOKEN"


@pytest.mark.parametrize(("method", "url"), ENDPOINTS)
def test_doctor_role_returns_403(client, method, url):
    response = getattr(client, method)(url, headers={"Authorization": "Bearer tok-doctor"})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"


def test_receptionist_is_allowed(client, reception_headers):
    assert client.get("/api/reception/appointments", headers=reception_headers).status_code == 200


def test_admin_is_allowed(client, admin_headers):
    assert client.get("/api/reception/appointments", headers=admin_headers).status_code == 200


def test_default_verifier_rejects_every_token(client, reception_headers):
    security.set_token_verifier(None)

    response = client.get("/api/reception/appointments", headers=reception_headers)

    assert response.status_code == 401
