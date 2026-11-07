import pytest

from app import config, db

_CACHED = (config.get_settings, db.get_engine, db.get_session_factory)


@pytest.fixture(autouse=True)
def _reset_caches():
    """Xóa cache settings/engine để mỗi test dùng biến môi trường riêng."""
    for fn in _CACHED:
        fn.cache_clear()
    yield
    for fn in _CACHED:
        fn.cache_clear()


@pytest.fixture
def sqlite_url(monkeypatch):
    url = "sqlite+pysqlite:///:memory:"
    monkeypatch.setenv("DATABASE_URL", url)
    return url
