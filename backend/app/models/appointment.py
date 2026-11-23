"""Lịch hẹn và tin thông báo gắn với lịch hẹn.

Ngày/giờ khám lưu theo giờ Việt Nam (không kèm múi giờ); thời điểm đến lưu kèm múi giờ.
"""

import datetime as dt
from enum import StrEnum

from sqlalchemy import (
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

from app.core.db import Base
from app.models.catalog import Doctor, Specialty
from app.models.patient import PatientProfile


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


class NotificationStatus(StrEnum):
    PENDING = "pending"  # Chờ gửi
    SENT = "sent"  # Đã gửi
    FAILED = "failed"  # Lỗi (sau khi đã thử lại theo BR-TB-03)


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
