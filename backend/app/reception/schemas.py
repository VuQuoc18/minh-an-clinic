import datetime as dt
import re
import unicodedata
from typing import Literal, Self

from pydantic import BaseModel, field_validator, model_validator

from app.models import AppointmentStatus, Channel

MIN_BIRTH_DATE = dt.date(1900, 1, 1)  # BR-TK-08
_PHONE_RE = re.compile(r"^0[0-9]{9}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_phone(value: str) -> bool:
    return bool(_PHONE_RE.fullmatch(value))


class AppointmentOut(BaseModel):
    id: int
    code: str
    patient_name: str
    patient_phone: str
    doctor_id: int
    doctor_name: str
    specialty_name: str
    appt_date: dt.date
    start_time: dt.time
    end_time: dt.time
    status: AppointmentStatus
    channel: Channel
    queue_number: int | None
    has_failed_notification: bool
    can_check_in: bool
    check_in_block_reason: str | None


class SpecialtyOut(BaseModel):
    id: int
    name: str


class DoctorOut(BaseModel):
    id: int
    full_name: str
    specialty_id: int


class SuggestionOut(BaseModel):
    slot_id: int
    doctor_id: int
    doctor_name: str
    slot_date: dt.date
    start_time: dt.time
    end_time: dt.time
    is_walk_in_slot: bool


class SuggestionsOut(BaseModel):
    suggestions: list[SuggestionOut]
    message: str | None
    next_available_date: dt.date | None


class ProfileOut(BaseModel):
    id: int
    full_name: str
    birth_date: dt.date
    gender: str
    phone: str | None
    is_primary: bool


class NewProfile(BaseModel):
    """Hồ sơ mới của khách vãng lai; kiểm tra theo BR-TK-08."""

    full_name: str
    birth_date: dt.date
    gender: Literal["Nam", "Nữ"]
    phone: str
    email: str | None = None
    address: str | None = None

    @field_validator("full_name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        value = unicodedata.normalize("NFC", value).strip()
        if not 2 <= len(value) <= 100:
            raise ValueError("Họ tên dài từ 2 đến 100 ký tự.")
        if not all(ch.isalpha() or ch == " " for ch in value):
            raise ValueError("Họ tên chỉ gồm chữ cái và khoảng trắng.")
        return value

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, value: dt.date) -> dt.date:
        if value < MIN_BIRTH_DATE:
            raise ValueError("Ngày sinh không được trước 01/01/1900.")
        return value

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, value: str) -> str:
        if not is_valid_phone(value):
            raise ValueError("Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.")
        return value

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if len(value) > 254 or not _EMAIL_RE.fullmatch(value):
            raise ValueError("Email không đúng định dạng.")
        return value

    @field_validator("address")
    @classmethod
    def _check_address(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if len(value) > 255:
            raise ValueError("Địa chỉ tối đa 255 ký tự.")
        return value


class WalkInRequest(BaseModel):
    slot_id: int
    profile_id: int | None = None
    new_profile: NewProfile | None = None

    @model_validator(mode="after")
    def _exactly_one_profile(self) -> Self:
        if (self.profile_id is None) == (self.new_profile is None):
            raise ValueError("Chọn một hồ sơ có sẵn hoặc nhập hồ sơ mới, không chọn cả hai.")
        return self
