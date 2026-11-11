"""Dữ liệu mẫu CHỈ DÙNG KHI DEV để xem và review màn hình MH-TD-01 Tiếp đón (SCR-001).

Chạy sau `alembic upgrade head`:  python -m app.dev_seed
Toàn bộ là dữ liệu giả. Script chỉ chạy khi đã đặt DEV_STAFF_TOKEN (dấu hiệu môi trường dev) và
có thể chạy lại nhiều lần: lịch hẹn của hôm nay tạo theo thời điểm hiện tại, mục đã có thì bỏ qua.
"""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import get_now
from app.config import get_settings
from app.db import get_session_factory
from app.models import (
    SLOT_MINUTES,
    Appointment,
    AppointmentStatus,
    Channel,
    Doctor,
    Notification,
    PatientAccount,
    PatientProfile,
    Slot,
    SlotKind,
    Specialty,
)

GRID_START = dt.time(7, 0)
GRID_END = dt.time(17, 0)  # khung cuối bắt đầu 16:45
WALK_IN_TIMES = (dt.time(11, 0), dt.time(11, 15), dt.time(16, 30), dt.time(16, 45))
DAYS_AHEAD = 3  # tạo khung giờ cho hôm nay và 3 ngày sau (để thử gợi ý "ngày gần nhất còn trống")


def _get_or_create_specialty(db: Session, name: str, **fields) -> Specialty:
    obj = db.scalar(select(Specialty).where(Specialty.name == name))
    if obj is None:
        obj = Specialty(name=name, active=True, **fields)
        db.add(obj)
        db.flush()
    return obj


def _get_or_create_doctor(db: Session, name: str, specialty: Specialty) -> Doctor:
    obj = db.scalar(select(Doctor).where(Doctor.full_name == name))
    if obj is None:
        obj = Doctor(full_name=name, specialty_id=specialty.id, active=True)
        db.add(obj)
        db.flush()
    return obj


def _get_or_create_slot(db: Session, doctor: Doctor, day: dt.date, start: dt.time) -> Slot:
    obj = db.scalar(
        select(Slot).where(
            Slot.doctor_id == doctor.id, Slot.slot_date == day, Slot.start_time == start
        )
    )
    if obj is None:
        kind = SlotKind.WALK_IN if start in WALK_IN_TIMES else SlotKind.NORMAL
        obj = Slot(doctor_id=doctor.id, slot_date=day, start_time=start, kind=kind.value)
        db.add(obj)
        db.flush()
    return obj


def _get_or_create_profile(
    db: Session, name: str, phone: str, birth: dt.date, gender: str
) -> PatientProfile:
    account = db.scalar(select(PatientAccount).where(PatientAccount.phone == phone))
    if account is None:
        account = PatientAccount(phone=phone)
        db.add(account)
        db.flush()
    obj = db.scalar(select(PatientProfile).where(PatientProfile.account_id == account.id))
    if obj is None:
        obj = PatientProfile(
            account_id=account.id,
            full_name=name,
            birth_date=birth,
            gender=gender,
            phone=phone,
            is_primary=True,
        )
        db.add(obj)
        db.flush()
    return obj


def _end_time(day: dt.date, start: dt.time) -> dt.time:
    return (dt.datetime.combine(day, start) + dt.timedelta(minutes=SLOT_MINUTES)).time()


def _grid_times() -> list[dt.time]:
    current = dt.datetime.combine(dt.date.min, GRID_START)
    end = dt.datetime.combine(dt.date.min, GRID_END)
    times = []
    while current < end:
        times.append(current.time())
        current += dt.timedelta(minutes=SLOT_MINUTES)
    return times


def _floor_to_slot(moment: dt.datetime) -> dt.datetime:
    return moment.replace(
        minute=moment.minute - moment.minute % SLOT_MINUTES, second=0, microsecond=0
    )


def seed_dev_data(db: Session, now: dt.datetime) -> int:
    """Tạo dữ liệu mẫu; trả về số lịch hẹn mới tạo cho hôm nay."""
    today = now.date()
    base = _floor_to_slot(now).replace(tzinfo=None)

    internal = _get_or_create_specialty(db, "Nội tổng quát")
    pediatrics = _get_or_create_specialty(db, "Nhi", max_age_exclusive=16)
    obgyn = _get_or_create_specialty(db, "Sản phụ khoa", required_gender="Nữ")
    doc_a = _get_or_create_doctor(db, "BS. Trần Minh Khoa", internal)
    doc_b = _get_or_create_doctor(db, "BS. Lê Thu Hoa", internal)
    doc_c = _get_or_create_doctor(db, "BS. Phạm Gia Bảo", pediatrics)
    doc_d = _get_or_create_doctor(db, "BS. Võ Ngọc Lan", obgyn)

    for doctor in (doc_a, doc_b, doc_c, doc_d):
        for offset in range(DAYS_AHEAD + 1):
            for start in _grid_times():
                _get_or_create_slot(db, doctor, today + dt.timedelta(days=offset), start)

    an = _get_or_create_profile(db, "Nguyễn Văn An", "0900000001", dt.date(1990, 5, 20), "Nam")
    binh = _get_or_create_profile(db, "Trần Thị Bình", "0900000002", dt.date(1985, 3, 2), "Nữ")
    cuong = _get_or_create_profile(db, "Lê Quốc Cường", "0900000003", dt.date(1978, 11, 8), "Nam")
    dung = _get_or_create_profile(db, "Phạm Thùy Dung", "0900000004", dt.date(2018, 7, 15), "Nữ")
    em = _get_or_create_profile(db, "Hoàng Minh Em", "0900000005", dt.date(1995, 1, 30), "Nam")
    huong = _get_or_create_profile(db, "Đỗ Thị Hương", "0900000006", dt.date(1992, 9, 12), "Nữ")

    # (phút lệch so với bây giờ, bác sĩ, hồ sơ, trạng thái, số thứ tự, tin gửi lỗi)
    scenarios = [
        (0, doc_a, an, AppointmentStatus.BOOKED, None, False),  # bấm "Xác nhận đến" được
        (15, doc_b, binh, AppointmentStatus.BOOKED, None, False),  # còn trong cửa sổ
        (-45, doc_a, cuong, AppointmentStatus.BOOKED, None, False),  # quá 15 phút sau giờ hẹn: khóa
        (180, doc_b, em, AppointmentStatus.BOOKED, None, False),  # sớm hơn 60 phút: khóa
        (-90, doc_a, huong, AppointmentStatus.ARRIVED, 1, False),  # đã đến, có số thứ tự
        (30, doc_c, dung, AppointmentStatus.BOOKED, None, True),  # tin thông báo gửi lỗi
        (-60, doc_d, binh, AppointmentStatus.CANCELLED, None, False),  # đã hủy
    ]
    created = 0
    for number, (offset, doctor, profile, status, queue, failed) in enumerate(scenarios, start=1):
        start_at = base + dt.timedelta(minutes=offset)
        if start_at.date() != today:
            continue
        slot = _get_or_create_slot(db, doctor, today, start_at.time())
        code = f"LH-{today:%y%m%d}-{number:04d}"
        taken = db.scalar(select(Appointment.id).where(Appointment.slot_id == slot.id))
        if taken is not None or db.scalar(select(Appointment.id).where(Appointment.code == code)):
            continue
        appointment = Appointment(
            code=code,
            profile_id=profile.id,
            specialty_id=doctor.specialty_id,
            doctor_id=doctor.id,
            slot_id=slot.id,
            appt_date=today,
            start_time=slot.start_time,
            end_time=(
                dt.datetime.combine(today, slot.start_time) + dt.timedelta(minutes=SLOT_MINUTES)
            ).time(),
            status=status.value,
            channel=Channel.ONLINE.value,
            created_by=1,
            queue_number=queue,
            arrived_at=now if status is AppointmentStatus.ARRIVED else None,
            checked_in_by=1 if status is AppointmentStatus.ARRIVED else None,
        )
        db.add(appointment)
        db.flush()
        if failed:
            db.add(
                Notification(
                    appointment_id=appointment.id,
                    kind="booked",
                    channel="sms",
                    status="failed",
                    attempts=3,
                )
            )
        created += 1
    db.commit()
    return created


def main() -> None:
    settings = get_settings()
    if not settings.dev_staff_token:
        raise SystemExit("Từ chối chạy: chỉ seed khi đã đặt DEV_STAFF_TOKEN (môi trường dev).")
    with get_session_factory()() as db:
        created = seed_dev_data(db, get_now())
    print(f"Đã tạo {created} lịch hẹn mẫu cho hôm nay.")  # noqa: T201


if __name__ == "__main__":  # pragma: no cover
    main()
