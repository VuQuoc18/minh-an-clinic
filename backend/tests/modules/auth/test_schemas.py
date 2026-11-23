import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import MAX_PASSWORD_LENGTH, LoginRequest


def test_valid_request_is_accepted():
    req = LoginRequest(so_dien_thoai="0912345678", mat_khau="x")
    assert req.so_dien_thoai == "0912345678"


@pytest.mark.parametrize(
    "phone",
    ["", "091234567", "09123456789", "1912345678", "091234567a", " 0912345678", "0912 345678"],
)
def test_invalid_phone_is_rejected(phone):
    with pytest.raises(ValidationError, match="10 chữ số"):
        LoginRequest(so_dien_thoai=phone, mat_khau="x")


def test_empty_password_is_rejected():
    with pytest.raises(ValidationError):
        LoginRequest(so_dien_thoai="0912345678", mat_khau="")


def test_password_length_limit_is_inclusive():
    LoginRequest(so_dien_thoai="0912345678", mat_khau="a" * MAX_PASSWORD_LENGTH)
    with pytest.raises(ValidationError):
        LoginRequest(so_dien_thoai="0912345678", mat_khau="a" * (MAX_PASSWORD_LENGTH + 1))


def test_short_password_is_not_checked_against_br_tk_09():
    # Quy định 8 ký tự có cả chữ và số chỉ áp dụng khi đặt mật khẩu (MH-TK-05).
    assert LoginRequest(so_dien_thoai="0912345678", mat_khau="a").mat_khau == "a"
