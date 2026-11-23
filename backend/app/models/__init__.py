"""Model dữ liệu dùng chung cho mọi phân hệ.

Import gói này để đăng ký toàn bộ bảng vào `Base.metadata` (Alembic dùng để so sánh schema).
"""

from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    Channel,
    Notification,
    NotificationStatus,
)
from app.models.catalog import SLOT_MINUTES, Doctor, Slot, SlotKind, Specialty
from app.models.patient import LoginThrottle, PatientAccount, PatientProfile, PatientSession

__all__ = [
    "SLOT_MINUTES",
    "Appointment",
    "AppointmentStatus",
    "Channel",
    "Doctor",
    "LoginThrottle",
    "Notification",
    "NotificationStatus",
    "PatientAccount",
    "PatientProfile",
    "PatientSession",
    "Slot",
    "SlotKind",
    "Specialty",
]
