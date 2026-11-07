import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import Base, get_db, get_engine, get_session_factory


def test_get_engine_uses_database_url_and_is_cached(sqlite_url):
    engine = get_engine()

    assert engine.url.drivername == "sqlite+pysqlite"
    assert engine.url.database == ":memory:"
    assert get_engine() is engine


def test_get_db_yields_working_session(sqlite_url):
    gen = get_db()
    session = next(gen)

    assert isinstance(session, Session)
    assert session.execute(text("SELECT 1")).scalar() == 1
    gen.close()


def test_get_db_closes_session_after_request(sqlite_url, monkeypatch):
    closed = []
    session = get_session_factory()()
    monkeypatch.setattr(session, "close", lambda: closed.append(True))
    monkeypatch.setattr("app.db.get_session_factory", lambda: lambda: session)

    gen = get_db()
    next(gen)
    gen.close()

    assert closed == [True]


def test_get_db_closes_session_when_request_raises(sqlite_url, monkeypatch):
    closed = []
    session = get_session_factory()()
    monkeypatch.setattr(session, "close", lambda: closed.append(True))
    monkeypatch.setattr("app.db.get_session_factory", lambda: lambda: session)

    gen = get_db()
    next(gen)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))

    assert closed == [True]


def test_get_engine_without_database_url_raises(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        get_engine()


def test_base_metadata_starts_empty():
    assert Base.metadata.tables == {}
