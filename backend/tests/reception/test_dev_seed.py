import datetime as dt

import pytest
from sqlalchemy import func, select

from app import dev_seed
from app.models import Appointment, Notification, Slot, Specialty
from tests.reception.conftest import NOW


def test_seed_creates_catalog_slots_and_appointments(db):
    created = dev_seed.seed_dev_data(db, NOW)

    assert created == 7
    assert db.scalar(select(func.count()).select_from(Specialty)) == 3
    assert db.scalar(select(func.count()).select_from(Slot)) > 0
    assert db.scalar(select(func.count()).select_from(Notification)) == 1


def test_seed_is_idempotent(db):
    dev_seed.seed_dev_data(db, NOW)
    total = db.scalar(select(func.count()).select_from(Appointment))

    created_again = dev_seed.seed_dev_data(db, NOW)

    assert created_again == 0
    assert db.scalar(select(func.count()).select_from(Appointment)) == total


def test_seed_marks_walk_in_slots(db):
    dev_seed.seed_dev_data(db, NOW)

    kinds = set(db.scalars(select(Slot.kind).where(Slot.start_time == dt.time(11, 0))))

    assert kinds == {"walk_in"}


def test_seed_skips_appointments_that_fall_on_another_day(db):
    late = NOW.replace(hour=23, minute=50)

    created = dev_seed.seed_dev_data(db, late)

    assert created < 7


def test_main_refuses_without_dev_token(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.delenv("DEV_STAFF_TOKEN", raising=False)

    with pytest.raises(SystemExit, match="DEV_STAFF_TOKEN"):
        dev_seed.main()


def test_main_seeds_when_dev_token_is_set(monkeypatch, db, capsys):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("DEV_STAFF_TOKEN", "dev-token")
    monkeypatch.setattr(dev_seed, "get_session_factory", lambda: lambda: db)
    monkeypatch.setattr(dev_seed, "get_now", lambda: NOW)

    dev_seed.main()

    assert "7" in capsys.readouterr().out
