"""Tài khoản mẫu CHỈ DÙNG KHI DEV/SANDBOX để kiểm thử E2E thủ công đăng nhập bệnh nhân (SCR-005).

Chạy sau `alembic upgrade head`, trong thư mục backend:
    DEV_STAFF_TOKEN=... .venv/bin/python scripts/seed_e2e_login.py

Toàn bộ là dữ liệu giả. Script từ chối chạy khi chưa đặt DEV_STAFF_TOKEN (dấu hiệu môi trường dev)
và chạy lại được nhiều lần: mỗi lần đặt lại 5 số dưới đây về đúng trạng thái ban đầu (mật khẩu,
hồ sơ chính chủ, phiên) và xóa bộ đếm sai và khóa đăng nhập của chúng. Không đụng tới số khác.
"""

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models import LoginThrottle, PatientAccount, PatientProfile, PatientSession
from app.modules.auth.passwords import hash_password

PASSWORD = "Test1234"  # mật khẩu giả cho môi trường dev
PROFILE_NAME = "Nguyễn Văn E2E"


@dataclass(frozen=True)
class SeedAccount:
    phone: str
    has_password: bool
    has_primary_profile: bool
    note: str


ACCOUNTS = (
    SeedAccount("0901000001", True, False, "có mật khẩu, chưa có hồ sơ chính chủ"),
    SeedAccount("0901000002", True, True, "có mật khẩu, đã có hồ sơ chính chủ"),
    SeedAccount("0901000003", False, False, "chưa có mật khẩu (lễ tân tạo hộ)"),
    SeedAccount("0901000004", True, False, "thử khóa sau 5 lần sai"),
    SeedAccount("0901000005", True, False, "kiểm tra khóa theo từng số"),
)


def seed_login_accounts(db: Session) -> list[SeedAccount]:
    """Tạo hoặc đặt lại các tài khoản mẫu; trả về danh sách đã xử lý."""
    phones = [item.phone for item in ACCOUNTS]
    db.execute(delete(LoginThrottle).where(LoginThrottle.phone.in_(phones)))
    for item in ACCOUNTS:
        account = db.scalar(select(PatientAccount).where(PatientAccount.phone == item.phone))
        if account is None:
            account = PatientAccount(phone=item.phone)
            db.add(account)
            db.flush()
        account.password_hash = hash_password(PASSWORD) if item.has_password else None
        db.execute(delete(PatientSession).where(PatientSession.account_id == account.id))
        db.execute(delete(PatientProfile).where(PatientProfile.account_id == account.id))
        if item.has_primary_profile:
            db.add(
                PatientProfile(
                    account_id=account.id,
                    full_name=PROFILE_NAME,
                    birth_date=dt.date(1990, 1, 1),
                    gender="Nam",
                    phone=item.phone,
                    is_primary=True,
                )
            )
    db.commit()
    return list(ACCOUNTS)


def main() -> None:
    if not get_settings().dev_staff_token:
        raise SystemExit("Từ chối chạy: chỉ seed khi đã đặt DEV_STAFF_TOKEN (môi trường dev).")
    with get_session_factory()() as db:
        done = seed_login_accounts(db)
    for item in done:
        print(f"{item.phone}  {item.note}")
    print(f"Mật khẩu của các số có mật khẩu: {PASSWORD}")


if __name__ == "__main__":
    main()
