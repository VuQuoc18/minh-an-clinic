import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    # Tránh đọc nhầm file .env thật trong thư mục chạy test.
    monkeypatch.chdir(tmp_path)


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    assert get_settings().database_url == "sqlite:///:memory:"


def test_settings_defaults_timezone_and_log_level(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.delenv("TIMEZONE", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = get_settings()

    assert settings.timezone == "Asia/Ho_Chi_Minh"
    assert settings.log_level == "INFO"


def test_settings_env_overrides_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    assert get_settings().log_level == "DEBUG"


def test_settings_missing_database_url_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings()


def test_settings_empty_database_url_is_accepted_as_string(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")

    assert Settings().database_url == ""


def test_settings_reads_from_dotenv_file(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / ".env").write_text("DATABASE_URL=sqlite:///from-dotenv\n", encoding="utf-8")

    assert Settings().database_url == "sqlite:///from-dotenv"


def test_settings_ignores_unknown_env_keys_in_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / ".env").write_text(
        "DATABASE_URL=sqlite:///x\nPOSTGRES_PASSWORD=fake\n", encoding="utf-8"
    )

    assert Settings().database_url == "sqlite:///x"


def test_get_settings_is_cached(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    assert get_settings() is get_settings()
