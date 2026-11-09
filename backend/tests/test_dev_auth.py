from fastapi.testclient import TestClient

from app import auth
from app.main import app


def teardown_function():
    auth.set_token_verifier(None)


def test_dev_verifier_accepts_configured_token_as_receptionist():
    auth.install_dev_token_verifier("dev-token")

    staff = auth._verifier("dev-token")

    assert staff is not None
    assert staff.role == auth.Role.RECEPTIONIST.value


def test_dev_verifier_rejects_other_tokens():
    auth.install_dev_token_verifier("dev-token")

    assert auth._verifier("other") is None


def test_dev_verifier_without_token_keeps_reject_all_default():
    auth.install_dev_token_verifier(None)
    auth.install_dev_token_verifier("")

    assert auth._verifier("anything") is None


def test_lifespan_installs_dev_verifier_from_settings(monkeypatch, sqlite_url):
    monkeypatch.setenv("DEV_STAFF_TOKEN", "dev-token")

    with TestClient(app):
        assert auth._verifier("dev-token") is not None


def test_lifespan_without_dev_token_rejects_every_token(monkeypatch, sqlite_url):
    monkeypatch.delenv("DEV_STAFF_TOKEN", raising=False)

    with TestClient(app):
        assert auth._verifier("dev-token") is None
