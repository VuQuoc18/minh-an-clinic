"""Fixture dùng chung cho test màn hình Tiếp đón (SCR-001). Toàn bộ dữ liệu là dữ liệu giả."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth
from app.auth import Role, Staff
from app.clock import get_now
from app.db import Base, get_db
from app.main import app
from app.models import (
    Appointment,
    AppointmentStatus,
    Channel,
    Doctor,
    Notification,
    PatientAccount,
    PatientProfile,
    Slot,
    Specialty,
)

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
# Thứ Hai 09/11/2026, 09:00 giờ Việt Nam.
NOW = dt.datetime(2026, 11, 9, 9, 0, tzinfo=TZ)
TODAY = NOW.date()

RECEPTIONIST = Staff(id=1, role=Role.RECEPTIONIST.value)
ADMIN = Staff(id=2, role=Role.ADMIN.value)
DOCTOR = Staff(id=3, role=Role.DOCTOR.value)
TOKENS = {"tok-reception": RECEPTIONIST, "tok-admin": ADMIN, "tok-doctor": DOCTOR}


def at(hour: int, minute: int = 0) -> dt.time:
    return dt.time(hour, minute)


class Seeder:
    """Tạo dữ liệu giả vào DB test."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._phone = 900000000
        self._code = 0

    def specialty(self, name="Nội", max_age=None, gender=None, active=True) -> Specialty:
        obj = Specialty(name=name, active=active, max_age_exclusive=max_age, required_gender=gender)
        self.db.add(obj)
        self.db.commit()
        return obj

    def doctor(self, specialty: Specialty, name="Bác sĩ A", active=True) -> Doctor:
        obj = Doctor(full_name=name, specialty_id=specialty.id, active=active)
        self.db.add(obj)
        self.db.commit()
        return obj

    def slot(self, doctor, start, day=TODAY, kind="normal", blocked=False) -> Slot:
        obj = Slot(doctor_id=doctor.id, slot_date=day, start_time=start, kind=kind, blocked=blocked)
        self.db.add(obj)
        self.db.commit()
        return obj

    def profile(
        self,
        name="Nguyễn Văn An",
        phone="0912345678",
        birth=dt.date(1990, 5, 20),
        gender="Nam",
        hidden=False,
        account=None,
        primary=True,
    ) -> PatientProfile:
        if account is None:
            account = PatientAccount(phone=phone)
            self.db.add(account)
            self.db.flush()
        obj = PatientProfile(
            account_id=account.id,
            full_name=name,
            birth_date=birth,
            gender=gender,
            phone=phone,
            is_primary=primary,
            hidden=hidden,
        )
        self.db.add(obj)
        self.db.commit()
        return obj

    def appointment(
        self,
        profile,
        doctor,
        slot,
        status=AppointmentStatus.BOOKED,
        channel=Channel.RECEPTION,
        queue=None,
        code=None,
    ) -> Appointment:
        self._code += 1
        end = (
            dt.datetime.combine(slot.slot_date, slot.start_time) + dt.timedelta(minutes=15)
        ).time()
        obj = Appointment(
            code=code or f"LH-{slot.slot_date:%y%m%d}-{self._code:04d}",
            profile_id=profile.id,
            specialty_id=doctor.specialty_id,
            doctor_id=doctor.id,
            slot_id=slot.id,
            appt_date=slot.slot_date,
            start_time=slot.start_time,
            end_time=end,
            status=status.value,
            channel=channel.value,
            created_by=1,
            queue_number=queue,
        )
        self.db.add(obj)
        self.db.commit()
        return obj

    def notification(self, appt, status: str) -> Notification:
        obj = Notification(appointment_id=appt.id, kind="booked", channel="sms", status=status)
        self.db.add(obj)
        self.db.commit()
        return obj


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


@pytest.fixture(autouse=True)
def _timezone_env(sqlite_url):
    """to_local đọc múi giờ từ settings nên cần DATABASE_URL giả."""


@pytest.fixture
def clock():
    """Đồng hồ giả: test đổi `clock.now` để dịch thời điểm."""

    class Clock:
        now = NOW

    return Clock()


@pytest.fixture
def client(db, clock):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_now] = lambda: clock.now
    auth.set_token_verifier(TOKENS.get)
    yield TestClient(app)
    app.dependency_overrides.clear()
    auth.set_token_verifier(None)


@pytest.fixture
def reception_headers() -> dict[str, str]:
    return {"Authorization": "Bearer tok-reception"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer tok-admin"}
