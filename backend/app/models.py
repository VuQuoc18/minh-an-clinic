"""Model dữ liệu tối thiểu cho màn hình MH-TD-01 Tiếp đón (SCR-001).

Giờ lưu là giờ Việt Nam (naive) cho ngày/giờ khám; các mô-đun khác (TK, LK, LB, TB) sẽ mở rộng sau.
"""

import datetime as dt
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

SLOT_MINUTES = 15  # BR-LB-01: mỗi khung giờ dài 15 phút


class AppointmentStatus(StrEnum):
    BOOKED = "booked"  # Đã đặt
    ARRIVED = "arrived"  # Đã đến
    IN_PROGRESS = "in_progress"  # Đang khám
    COMPLETED = "completed"  # Đã khám
    CANCELLED = "cancelled"  # Đã hủy
    NO_SHOW = "no_show"  # Vắng hẹn


class Channel(StrEnum):
    ONLINE = "online"  # Trực tuyến
    RECEPTION = "reception"  # Lễ tân
    WALK_IN = "walk_in"  # Vãng lai


class SlotKind(StrEnum):
    NORMAL = "normal"
    WALK_IN = "walk_in"  # BR-LB-03: khung vãng lai


class NotificationStatus(StrEnum):
    PENDING = "pending"  # Chờ gửi
    SENT = "sent"  # Đã gửi
    FAILED = "failed"  # Lỗi (sau khi đã thử lại theo BR-TB-03)


class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # BR-LK-06: Nhi chỉ nhận dưới 16 tuổi (max_age_exclusive=16), Sản phụ khoa chỉ nhận Nữ.
    max_age_exclusive: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_gender: Mapped[str | None] = mapped_column(String(3), nullable=True)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    specialty: Mapped[Specialty] = relationship()


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("doctor_id", "slot_date", "start_time", name="uq_slots"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    slot_date: Mapped[dt.date] = mapped_column(Date)
    start_time: Mapped[dt.time] = mapped_column(Time)
    kind: Mapped[str] = mapped_column(String(10), default=SlotKind.NORMAL.value)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    doctor: Mapped[Doctor] = relationship()


class PatientAccount(Base):
    __tablename__ = "patient_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(10), unique=True)


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("patient_accounts.id"))
    full_name: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[dt.date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(3))
    phone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[PatientAccount] = relationship()


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        # Một khung giờ chỉ có một lịch chưa hủy (chống trùng khi hai lễ tân cùng chọn).
        Index(
            "uq_appointments_active_slot",
            "slot_id",
            unique=True,
            postgresql_where=text("status <> 'cancelled'"),
            sqlite_where=text("status <> 'cancelled'"),
        ),
        # BR-TD-02: số thứ tự duy nhất theo bác sĩ trong ngày.
        UniqueConstraint("doctor_id", "appt_date", "queue_number", name="uq_appointments_queue"),
        Index("ix_appointments_appt_date", "appt_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)  # LH-YYMMDD-NNNN
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"))
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"))
    appt_date: Mapped[dt.date] = mapped_column(Date)
    start_time: Mapped[dt.time] = mapped_column(Time)
    end_time: Mapped[dt.time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(12), default=AppointmentStatus.BOOKED.value)
    channel: Mapped[str] = mapped_column(String(10))
    created_by: Mapped[int] = mapped_column(Integer)
    arrived_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queue_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_in_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    profile: Mapped[PatientProfile] = relationship()
    specialty: Mapped[Specialty] = relationship()
    doctor: Mapped[Doctor] = relationship()


class Notification(Base):
    """Tin thông báo tối thiểu: chỉ để màn hình tiếp đón hiện cảnh báo tin lỗi (FR-TB-02)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    channel: Mapped[str] = mapped_column(String(10))  # sms | email
    status: Mapped[str] = mapped_column(String(10), default=NotificationStatus.PENDING.value)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
