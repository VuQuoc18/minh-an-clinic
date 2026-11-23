"""Nghiệp vụ màn hình MH-TK-01 Đăng nhập bệnh nhân (SCR-005): FR-TK-01, BR-TK-03, BR-TK-05."""

import datetime as dt
import hashlib
import logging
import secrets
from zoneinfo import ZoneInfo

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import LoginThrottle, PatientAccount, PatientProfile, PatientSession
from app.modules.auth.passwords import verify_password
from app.modules.auth.schemas import LoginOut

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 5  # BR-TK-03
LOCK_DURATION = dt.timedelta(minutes=15)  # BR-TK-03
SESSION_IDLE_DAYS = 30  # BR-TK-05

CODE_WRONG_CREDENTIALS = "SAI_THONG_TIN"
CODE_LOCKED = "BI_KHOA"


class LoginRejected(Exception):
    """Đăng nhập bị từ chối; router đổi thành phản hồi lỗi kèm các trường phụ."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        extra: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.extra = extra or {}


def _local(moment: dt.datetime) -> dt.datetime:
    return moment.astimezone(ZoneInfo(get_settings().timezone))


def _aware(moment: dt.datetime, reference: dt.datetime) -> dt.datetime:
    # SQLite trả datetime không kèm múi giờ; Postgres thì có. Coi giá trị trần là cùng múi với now.
    return moment if moment.tzinfo else moment.replace(tzinfo=reference.tzinfo)


def _locked(retry_at: dt.datetime) -> LoginRejected:
    shown = _local(retry_at)
    return LoginRejected(
        429,
        CODE_LOCKED,
        f"Số điện thoại bị khóa đăng nhập. Thử lại sau {shown:%H:%M} ngày {shown:%d/%m/%Y}.",
        {"thu_lai_luc": retry_at.isoformat()},
    )


def _wrong_credentials(remaining: int) -> LoginRejected:
    return LoginRejected(
        401,
        CODE_WRONG_CREDENTIALS,
        f"Số điện thoại hoặc mật khẩu không đúng. Còn {remaining} lần thử.",
        {"so_lan_con_lai": remaining},
    )


def _has_primary_profile(db: Session, account_id: int) -> bool:
    # Hồ sơ đã ẩn không tính (cần xác nhận lại theo Detail Design, bước 7).
    return bool(
        db.scalar(
            select(
                exists().where(
                    PatientProfile.account_id == account_id,
                    PatientProfile.is_primary.is_(True),
                    PatientProfile.hidden.is_(False),
                )
            )
        )
    )


def _create_session(db: Session, account_id: int, now: dt.datetime) -> tuple[str, dt.datetime]:
    token = secrets.token_urlsafe(32)
    db.add(
        PatientSession(
            account_id=account_id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            created_at=now,
            last_used_at=now,
            status="active",
        )
    )
    return token, now + dt.timedelta(days=SESSION_IDLE_DAYS)


def login(db: Session, phone: str, password: str, now: dt.datetime) -> LoginOut:
    """Các bước 2–8 của Detail Design (bước 1, kiểm tra định dạng, nằm ở ``LoginRequest``).

    Mọi thay đổi chỉ được commit khi đã có kết quả; lỗi hệ thống giữa chừng thì rollback nên
    không đổi bộ đếm.
    """
    try:
        return _login(db, phone, password, now)
    except LoginRejected:
        raise
    except Exception:
        db.rollback()
        logger.exception("Đăng nhập bệnh nhân lỗi hệ thống")
        raise


def _login(db: Session, phone: str, password: str, now: dt.datetime) -> LoginOut:
    throttle = db.scalar(
        select(LoginThrottle).where(LoginThrottle.phone == phone).with_for_update()
    )

    # Bước 2: đang khóa thì dừng, không kiểm tra mật khẩu. Hết khóa thì bộ đếm về 0.
    if throttle is not None and throttle.locked_until is not None:
        locked_until = _aware(throttle.locked_until, now)
        if now < locked_until:
            raise _locked(locked_until)
        throttle.failed_count = 0
        throttle.locked_until = None
        db.commit()

    # Bước 3–4: chỉ tìm trong tài khoản bệnh nhân; chưa có tài khoản hoặc chưa có mật khẩu.
    account = db.scalar(select(PatientAccount).where(PatientAccount.phone == phone))
    if account is None or not account.password_hash:
        return LoginOut(ket_qua="CHUA_CO_MAT_KHAU", so_dien_thoai=phone)

    # Bước 5: so mật khẩu.
    if not verify_password(password, account.password_hash):
        if throttle is None:
            throttle = LoginThrottle(phone=phone, failed_count=0)
            db.add(throttle)
        throttle.failed_count += 1
        if throttle.failed_count >= MAX_FAILED_ATTEMPTS:
            throttle.locked_until = now + LOCK_DURATION
            db.commit()
            raise _locked(throttle.locked_until)
        db.commit()
        raise _wrong_credentials(MAX_FAILED_ATTEMPTS - throttle.failed_count)

    if throttle is not None:
        throttle.failed_count = 0
        throttle.locked_until = None

    # Bước 6–8.
    token, expires_at = _create_session(db, account.id, now)
    can_create_profile = not _has_primary_profile(db, account.id)
    db.commit()
    return LoginOut(
        ket_qua="THANH_CONG",
        so_dien_thoai=phone,
        token=token,
        het_han_luc=expires_at,
        can_tao_ho_so=can_create_profile,
    )
