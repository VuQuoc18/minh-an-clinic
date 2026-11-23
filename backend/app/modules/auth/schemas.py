import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.reception.schemas import is_valid_phone

PHONE_MESSAGE = "Số điện thoại gồm 10 chữ số và bắt đầu bằng 0."  # BR-TK-08
MAX_PASSWORD_LENGTH = 128  # chặn mật khẩu quá dài làm tốn tài nguyên băm


class LoginRequest(BaseModel):
    """FR-TK-01: số điện thoại theo BR-TK-08; mật khẩu chỉ cần không trống."""

    so_dien_thoai: str
    mat_khau: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("so_dien_thoai")
    @classmethod
    def _check_phone(cls, value: str) -> str:
        if not is_valid_phone(value):
            raise ValueError(PHONE_MESSAGE)
        return value


class LoginOut(BaseModel):
    ket_qua: Literal["THANH_CONG", "CHUA_CO_MAT_KHAU"]
    so_dien_thoai: str
    # Chỉ có khi THANH_CONG.
    token: str | None = None
    het_han_luc: dt.datetime | None = None  # hết hạn nếu không dùng (BR-TK-05)
    can_tao_ho_so: bool = False  # true: chưa có hồ sơ chính chủ, đi tới form hồ sơ (FR-TK-02)
