"""Xác thực nhân viên (phương án A: giả lập).

Đăng nhập thật (FR-TK-04) chưa làm. Mặc định mọi token đều bị từ chối (fail closed); khi làm
FR-TK-04, thay bộ kiểm tra token bằng `set_token_verifier`. Test dùng token giả qua cùng cơ chế.
"""

import hmac
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class Role(StrEnum):
    RECEPTIONIST = "receptionist"  # Lễ tân
    ADMIN = "admin"  # Quản trị (quản lý phòng khám)
    DOCTOR = "doctor"  # Bác sĩ


@dataclass(frozen=True)
class Staff:
    id: int
    role: str


TokenVerifier = Callable[[str], Staff | None]


def _reject_all(_token: str) -> Staff | None:
    return None


_verifier: TokenVerifier = _reject_all


def set_token_verifier(verifier: TokenVerifier | None) -> None:
    """Đặt bộ kiểm tra token; None để quay về mặc định (từ chối tất cả)."""
    global _verifier
    _verifier = verifier or _reject_all


def install_dev_token_verifier(token: str | None) -> None:
    """Chỉ dev: token cấu hình sẵn đăng nhập như Lễ tân. Không có token thì giữ nguyên."""
    if not token:
        return
    dev_staff = Staff(id=1, role=Role.RECEPTIONIST.value)

    def verify(candidate: str) -> Staff | None:
        return dev_staff if hmac.compare_digest(candidate, token) else None

    set_token_verifier(verify)


_bearer = HTTPBearer(auto_error=False)


def _error(status_code: int, code: str, message: str) -> HTTPException:
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return HTTPException(status_code, {"code": code, "message": message}, headers=headers)


def get_current_staff(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Staff:
    if credentials is None:
        raise _error(401, "UNAUTHENTICATED", "Chưa đăng nhập.")
    staff = _verifier(credentials.credentials)
    if staff is None:
        raise _error(401, "INVALID_TOKEN", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")
    return staff


def require_role(*roles: Role) -> Callable[[Staff], Staff]:
    allowed = {role.value for role in roles}

    def dependency(staff: Annotated[Staff, Depends(get_current_staff)]) -> Staff:
        if staff.role not in allowed:
            raise _error(403, "FORBIDDEN", "Bạn không có quyền thực hiện thao tác này.")
        return staff

    return dependency
