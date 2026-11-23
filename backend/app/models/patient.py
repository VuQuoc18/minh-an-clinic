"""Tài khoản bệnh nhân (theo số điện thoại) và các hồ sơ thuộc tài khoản."""

import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PatientAccount(Base):
    __tablename__ = "patient_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(10), unique=True)
    # Mật khẩu đã băm (FR-TK-01); trống khi số mới hoặc do lễ tân tạo hộ, chưa đặt mật khẩu.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)


class LoginThrottle(Base):
    """Bộ đếm nhập sai mật khẩu liên tiếp và thời điểm hết khóa đăng nhập theo số điện thoại.

    BR-TK-03. Tách riêng với bộ đếm sai OTP.
    """

    __tablename__ = "patient_login_throttles"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(10), unique=True)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PatientSession(Base):
    """Phiên đăng nhập của bệnh nhân (BR-TK-05: hết hạn sau 30 ngày không dùng).

    Chỉ lưu băm SHA-256 của token, không lưu token gốc.
    """

    __tablename__ = "patient_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("patient_accounts.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(10), default="active")  # active | expired


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
