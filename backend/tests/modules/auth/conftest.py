"""Fixture dùng chung cho test màn hình Đăng nhập bệnh nhân (SCR-005). Toàn bộ dữ liệu là giả."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.clock import get_now
from app.core.db import Base, get_db
from app.main import app
from app.models import PatientAccount, PatientProfile
from app.modules.auth.passwords import hash_password

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
NOW = dt.datetime(2026, 11, 24, 9, 0, tzinfo=TZ)
PHONE = "0912345678"
PASSWORD = "matkhau123"  # mật khẩu giả cho test


class Seeder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def account(self, phone=PHONE, password: str | None = PASSWORD) -> PatientAccount:
        obj = PatientAccount(
            phone=phone, password_hash=hash_password(password) if password else None
        )
        self.db.add(obj)
        self.db.commit()
        return obj

    def profile(self, account, primary=True, hidden=False) -> PatientProfile:
        obj = PatientProfile(
            account_id=account.id,
            full_name="Nguyễn Văn An",
            birth_date=dt.date(1990, 5, 20),
            gender="Nam",
            phone=account.phone,
            is_primary=primary,
            hidden=hidden,
        )
        self.db.add(obj)
        self.db.commit()
        return obj


@pytest.fixture(autouse=True)
def _env(sqlite_url):
    """service đọc múi giờ từ settings nên cần DATABASE_URL giả."""


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def seed(db) -> Seeder:
    return Seeder(db)


@pytest.fixture
def clock():
    class Clock:
        now = NOW

    return Clock()


@pytest.fixture
def client(db, clock):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_now] = lambda: clock.now
    yield TestClient(app)
    app.dependency_overrides.clear()
