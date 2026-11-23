"""Danh mục phòng khám: chuyên khoa, bác sĩ và khung giờ khám."""

import datetime as dt
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

SLOT_MINUTES = 15  # BR-LB-01: mỗi khung giờ dài 15 phút


class SlotKind(StrEnum):
    NORMAL = "normal"
    WALK_IN = "walk_in"  # BR-LB-03: khung vãng lai


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
