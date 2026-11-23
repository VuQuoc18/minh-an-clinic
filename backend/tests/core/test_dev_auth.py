from fastapi.testclient import TestClient

from app.core import security
from app.main import app


def teardown_function():
    security.set_token_verifier(None)


def test_dev_verifier_accepts_configured_token_as_receptionist():
    security.install_dev_token_verifier("dev-token")

    staff = security._verifier("dev-token")

    assert staff is not None
    assert staff.role == security.Role.RECEPTIONIST.value


def test_dev_verifier_rejects_other_tokens():
    security.install_dev_token_verifier("dev-token")

    assert security._verifier("other") is None


def test_dev_verifier_without_token_keeps_reject_all_default():
    security.install_dev_token_verifier(None)
    security.install_dev_token_verifier("")

    assert security._verifier("anything") is None


def test_lifespan_installs_dev_verifier_from_settings(monkeypatch, sqlite_url):
    monkeypatch.setenv("DEV_STAFF_TOKEN", "dev-token")

    with TestClient(app):
        assert security._verifier("dev-token") is not None


def test_lifespan_without_dev_token_rejects_every_token(monkeypatch, sqlite_url):
    monkeypatch.delenv("DEV_STAFF_TOKEN", raising=False)

    with TestClient(app):
        assert security._verifier("dev-token") is None
