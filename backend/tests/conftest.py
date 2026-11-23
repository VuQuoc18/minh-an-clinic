import os

import pytest

# Settings bắt buộc DATABASE_URL và `app.main` tạo app ngay khi import, nên đặt giá trị giả trước
# khi các module test được nạp. Test nào cần thiếu biến này thì tự `monkeypatch.delenv`.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.core import config, db

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
