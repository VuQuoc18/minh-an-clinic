"""Nghiệp vụ màn hình MH-TD-01 Tiếp đón (SCR-001): FR-TD-01, FR-TD-02, FR-TB-02 (cảnh báo)."""

import datetime as dt
import unicodedata
from zoneinfo import ZoneInfo

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import Staff
from app.config import get_settings
from app.models import (
    SLOT_MINUTES,
    Appointment,
    AppointmentStatus,
    Channel,
    Doctor,
    Notification,
    NotificationStatus,
    PatientAccount,
    PatientProfile,
    Slot,
    Specialty,
)
from app.reception.errors import ReceptionError
from app.reception.schemas import (
    AppointmentOut,
    NewProfile,
    SuggestionOut,
    SuggestionsOut,
    WalkInRequest,
    is_valid_phone,
)

CHECK_IN_EARLY = dt.timedelta(minutes=60)  # BR-TD-01
CHECK_IN_LATE = dt.timedelta(minutes=15)  # BR-TD-01
BOOKING_WINDOW_DAYS = 30  # BR-LK-01: hôm nay là ngày thứ nhất
MAX_VISIBLE_PROFILES = 5  # BR-TK-04
NHI_MAX_AGE_EXCLUSIVE = 16  # BR-LK-06
_MAX_ATTEMPTS = 5


# ---------- tiện ích ----------


def to_local(now: dt.datetime) -> dt.datetime:
    """Đổi về giờ phòng khám (không kèm múi giờ) để so với ngày giờ khám đã lưu."""
    if now.tzinfo is None:
        return now
    return now.astimezone(ZoneInfo(get_settings().timezone)).replace(tzinfo=None)


def fold(text: str) -> str:
    """Bỏ dấu, hạ chữ thường để so khớp họ tên không phân biệt dấu."""
    text = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())


def _start_dt(appt: Appointment) -> dt.datetime:
    return dt.datetime.combine(appt.appt_date, appt.start_time)


def check_in_state(appt: Appointment, now: dt.datetime) -> tuple[bool, str | None]:
    """BR-TD-01: bấm được từ 60 phút trước tới 15 phút sau giờ bắt đầu (đóng hai đầu)."""
    local = to_local(now)
    if appt.status != AppointmentStatus.BOOKED.value:
        return False, "Lịch hẹn không ở trạng thái Đã đặt."
    start = _start_dt(appt)
    opens = start - CHECK_IN_EARLY
    closes = start + CHECK_IN_LATE
    if local < opens:
        return False, f"Chưa đến giờ xác nhận. Mở lúc {opens:%H:%M}."
    if local > closes:
        return False, (
            f"Đã quá hạn xác nhận lúc {closes:%H:%M}. Hãy tiếp bệnh nhân như khách vãng lai."
        )
    return True, None


def _to_out(appt: Appointment, now: dt.datetime, failed_ids: set[int]) -> AppointmentOut:
    can, reason = check_in_state(appt, now)
    profile = appt.profile
    return AppointmentOut(
        id=appt.id,
        code=appt.code,
        patient_name=profile.full_name,
        patient_phone=profile.phone or profile.account.phone,
        doctor_id=appt.doctor_id,
        doctor_name=appt.doctor.full_name,
        specialty_name=appt.specialty.name,
        appt_date=appt.appt_date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        status=AppointmentStatus(appt.status),
        channel=Channel(appt.channel),
        queue_number=appt.queue_number,
        has_failed_notification=appt.id in failed_ids,
        can_check_in=can,
        check_in_block_reason=reason,
    )


def _load_appointment_options():
    return (
        joinedload(Appointment.profile).joinedload(PatientProfile.account),
        joinedload(Appointment.doctor),
        joinedload(Appointment.specialty),
    )


def _failed_notification_ids(db: Session, appt_ids: list[int]) -> set[int]:
    if not appt_ids:
        return set()
    rows = db.scalars(
        select(Notification.appointment_id)
        .where(Notification.appointment_id.in_(appt_ids))
        .where(Notification.status == NotificationStatus.FAILED.value)
    )
    return set(rows)


def _next_queue_number(db: Session, doctor_id: int, day: dt.date) -> int:
    """BR-TD-02: đánh riêng theo bác sĩ trong ngày, bắt đầu từ 1."""
    current = db.scalar(
        select(func.max(Appointment.queue_number))
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.appt_date == day)
    )
    return (current or 0) + 1


def _slot_is_taken(db: Session, slot_id: int) -> bool:
    return bool(
        db.scalar(
            select(
                exists()
                .where(Appointment.slot_id == slot_id)
                .where(Appointment.status != AppointmentStatus.CANCELLED.value)
            )
        )
    )


# ---------- danh sách và tìm kiếm ----------


def _matches(appt: Appointment, query: str) -> bool:
    upper = query.upper()
    if upper in appt.code:
        return True
    digits = query.replace(" ", "").replace(".", "")
    if digits.isdigit():
        phones = (appt.profile.phone or "", appt.profile.account.phone)
        if any(digits in phone for phone in phones):
            return True
    return fold(query) in fold(appt.profile.full_name)


def list_today(
    db: Session,
    now: dt.datetime,
    query: str | None = None,
    doctor_id: int | None = None,
    status: AppointmentStatus | None = None,
) -> list[AppointmentOut]:
    """Lịch hẹn của hôm nay, lọc theo ô tìm, bác sĩ, trạng thái (FR-TD-01)."""
    today = to_local(now).date()
    stmt = (
        select(Appointment)
        .options(*_load_appointment_options())
        .where(Appointment.appt_date == today)
        .order_by(Appointment.start_time, Appointment.id)
    )
    if doctor_id is not None:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if status is not None:
        stmt = stmt.where(Appointment.status == status.value)
    appts = list(db.scalars(stmt).unique())
    query = (query or "").strip()
    if query:
        appts = [a for a in appts if _matches(a, query)]
    failed = _failed_notification_ids(db, [a.id for a in appts])
    return [_to_out(a, now, failed) for a in appts]


def list_specialties(db: Session) -> list[Specialty]:
    return list(db.scalars(select(Specialty).where(Specialty.active).order_by(Specialty.name)))


def list_doctors(db: Session) -> list[Doctor]:
    return list(db.scalars(select(Doctor).where(Doctor.active).order_by(Doctor.full_name)))


# ---------- xác nhận đến (FR-TD-01) ----------


def check_in(db: Session, appointment_id: int, now: dt.datetime, staff: Staff) -> AppointmentOut:
    for _ in range(_MAX_ATTEMPTS):
        appt = db.scalar(
            select(Appointment)
            .options(*_load_appointment_options())
            .where(Appointment.id == appointment_id)
        )
        if appt is None:
            raise ReceptionError(404, "APPOINTMENT_NOT_FOUND", "Không tìm thấy lịch hẹn.")
        if appt.status != AppointmentStatus.BOOKED.value:
            raise ReceptionError(
                409, "INVALID_STATUS", "Lịch hẹn không ở trạng thái Đã đặt nên không xác nhận đến."
            )
        can, reason = check_in_state(appt, now)
        if not can:
            raise ReceptionError(409, "OUTSIDE_CHECK_IN_WINDOW", reason or "")
        appt.status = AppointmentStatus.ARRIVED.value
        appt.arrived_at = now
        appt.checked_in_by = staff.id
        appt.queue_number = _next_queue_number(db, appt.doctor_id, appt.appt_date)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()  # trùng số thứ tự do hai lễ tân cùng bấm: cấp lại số
            continue
        failed = _failed_notification_ids(db, [appt.id])
        return _to_out(appt, now, failed)
    raise ReceptionError(409, "QUEUE_CONFLICT", "Không cấp được số thứ tự. Vui lòng thử lại.")


# ---------- khách vãng lai (FR-TD-02) ----------


def _free_slots_stmt():
    return (
        select(Slot)
        .join(Doctor, Doctor.id == Slot.doctor_id)
        .where(Doctor.active)
        .where(~Slot.blocked)
        .where(
            ~exists()
            .where(Appointment.slot_id == Slot.id)
            .where(Appointment.status != AppointmentStatus.CANCELLED.value)
        )
    )


def _get_specialty(db: Session, specialty_id: int) -> Specialty:
    specialty = db.get(Specialty, specialty_id)
    if specialty is None or not specialty.active:
        raise ReceptionError(404, "SPECIALTY_NOT_FOUND", "Không tìm thấy chuyên khoa.")
    return specialty


def suggest_walk_in_slots(db: Session, specialty_id: int, now: dt.datetime) -> SuggestionsOut:
    """Khung trống sớm nhất của từng bác sĩ trong chuyên khoa, kể cả khung vãng lai."""
    _get_specialty(db, specialty_id)
    local = to_local(now)
    today = local.date()
    base = _free_slots_stmt().where(Doctor.specialty_id == specialty_id)

    todays = db.scalars(
        base.options(joinedload(Slot.doctor))
        .where(Slot.slot_date == today)
        .where(Slot.start_time >= local.time())
        .order_by(Slot.start_time, Slot.id)
    ).unique()
    earliest: dict[int, Slot] = {}
    for slot in todays:
        earliest.setdefault(slot.doctor_id, slot)
    chosen = sorted(earliest.values(), key=lambda s: (s.start_time, s.doctor.full_name))
    if chosen:
        return SuggestionsOut(
            suggestions=[_to_suggestion(s) for s in chosen],
            message=None,
            next_available_date=None,
        )

    last_day = today + dt.timedelta(days=BOOKING_WINDOW_DAYS - 1)
    next_date = db.scalar(
        base.with_only_columns(func.min(Slot.slot_date))
        .where(Slot.slot_date > today)
        .where(Slot.slot_date <= last_day)
    )
    return SuggestionsOut(suggestions=[], message="Hết chỗ hôm nay", next_available_date=next_date)


def _to_suggestion(slot: Slot) -> SuggestionOut:
    start = dt.datetime.combine(slot.slot_date, slot.start_time)
    return SuggestionOut(
        slot_id=slot.id,
        doctor_id=slot.doctor_id,
        doctor_name=slot.doctor.full_name,
        slot_date=slot.slot_date,
        start_time=slot.start_time,
        end_time=(start + dt.timedelta(minutes=SLOT_MINUTES)).time(),
        is_walk_in_slot=slot.kind == "walk_in",
    )


def search_profiles(db: Session, phone: str) -> list[PatientProfile]:
    """FR-LK-06: tìm hồ sơ theo số điện thoại (của tài khoản hoặc của hồ sơ), bỏ hồ sơ đã ẩn."""
    if not is_valid_phone(phone):
        raise ReceptionError(422, "INVALID_PHONE", "Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.")
    account_ids = select(PatientAccount.id).where(PatientAccount.phone == phone)
    stmt = (
        select(PatientProfile)
        .options(joinedload(PatientProfile.account))
        .where(~PatientProfile.hidden)
        .where((PatientProfile.account_id.in_(account_ids)) | (PatientProfile.phone == phone))
        .order_by(PatientProfile.is_primary.desc(), PatientProfile.full_name)
    )
    return list(db.scalars(stmt).unique())


def _age_on(birth: dt.date, day: dt.date) -> int:
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def _check_specialty_rule(specialty: Specialty, birth: dt.date, gender: str, day: dt.date) -> None:
    """BR-LK-06: Nhi dưới 16 tuổi tại ngày khám, Sản phụ khoa chỉ nữ."""
    if (
        specialty.max_age_exclusive is not None
        and _age_on(birth, day) >= specialty.max_age_exclusive
    ):
        raise ReceptionError(
            409,
            "SPECIALTY_AGE_RESTRICTED",
            f"Chuyên khoa {specialty.name} chỉ nhận hồ sơ dưới {specialty.max_age_exclusive} tuổi.",
        )
    if specialty.required_gender is not None and gender != specialty.required_gender:
        raise ReceptionError(
            409,
            "SPECIALTY_GENDER_RESTRICTED",
            f"Chuyên khoa {specialty.name} chỉ nhận hồ sơ giới tính {specialty.required_gender}.",
        )


def _check_conflicts(db: Session, profile: PatientProfile, slot: Slot, specialty_id: int) -> None:
    """BR-LK-02: không trùng ngày + chuyên khoa, không chồng giờ (lịch chưa hủy)."""
    same_day = db.scalars(
        select(Appointment)
        .where(Appointment.profile_id == profile.id)
        .where(Appointment.appt_date == slot.slot_date)
        .where(Appointment.status != AppointmentStatus.CANCELLED.value)
    ).all()
    new_start = dt.datetime.combine(slot.slot_date, slot.start_time)
    new_end = new_start + dt.timedelta(minutes=SLOT_MINUTES)
    for other in same_day:
        if other.specialty_id == specialty_id:
            raise ReceptionError(
                409,
                "DUPLICATE_SAME_DAY_SPECIALTY",
                "Hồ sơ đã có lịch hẹn chưa hủy cùng ngày và cùng chuyên khoa.",
            )
        if _start_dt(other) < new_end and new_start < dt.datetime.combine(
            other.appt_date, other.end_time
        ):
            raise ReceptionError(
                409, "OVERLAPPING_APPOINTMENT", "Hồ sơ đã có lịch hẹn chồng giờ với khung này."
            )


def _resolve_profile(db: Session, req: WalkInRequest, today: dt.date) -> PatientProfile:
    if req.profile_id is not None:
        profile = db.scalar(
            select(PatientProfile)
            .options(joinedload(PatientProfile.account))
            .where(PatientProfile.id == req.profile_id)
            .where(~PatientProfile.hidden)
        )
        if profile is None:
            raise ReceptionError(404, "PROFILE_NOT_FOUND", "Không tìm thấy hồ sơ bệnh nhân.")
        return profile
    assert req.new_profile is not None
    if req.new_profile.birth_date > today:  # BR-TK-08: không sau ngày hôm nay
        raise ReceptionError(422, "BIRTH_DATE_IN_FUTURE", "Ngày sinh không được sau ngày hôm nay.")
    return _create_profile(db, req.new_profile)


def _create_profile(db: Session, data: NewProfile) -> PatientProfile:
    account = db.scalar(select(PatientAccount).where(PatientAccount.phone == data.phone))
    if account is None:
        account = PatientAccount(phone=data.phone)
        db.add(account)
        db.flush()
    visible = db.scalars(
        select(PatientProfile)
        .where(PatientProfile.account_id == account.id)
        .where(~PatientProfile.hidden)
    ).all()
    for existing in visible:  # cùng họ tên và ngày sinh thì dùng lại, không tạo trùng
        if (
            fold(existing.full_name) == fold(data.full_name)
            and existing.birth_date == data.birth_date
        ):
            return existing
    if len(visible) >= MAX_VISIBLE_PROFILES:
        raise ReceptionError(
            409,
            "PROFILE_LIMIT_REACHED",
            f"Tài khoản đã đủ {MAX_VISIBLE_PROFILES} hồ sơ đang hiện.",
        )
    profile = PatientProfile(
        account_id=account.id,
        full_name=data.full_name,
        birth_date=data.birth_date,
        gender=data.gender,
        phone=data.phone,
        email=data.email,
        address=data.address,
        is_primary=not visible,
        hidden=False,
    )
    profile.account = account
    db.add(profile)
    db.flush()
    return profile


def _next_code(db: Session, day: dt.date) -> str:
    """BR-LK-07: LH-YYMMDD-NNNN, NNNN là số thứ tự tạo trong ngày từ 0001."""
    prefix = f"LH-{day:%y%m%d}-"
    last = db.scalar(select(func.max(Appointment.code)).where(Appointment.code.like(f"{prefix}%")))
    number = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{prefix}{number:04d}"


def create_walk_in(
    db: Session, req: WalkInRequest, now: dt.datetime, staff: Staff
) -> AppointmentOut:
    """Tạo lịch kênh Vãng lai và chuyển ngay sang Đã đến kèm số thứ tự. Không gửi thông báo."""
    local = to_local(now)
    for _ in range(_MAX_ATTEMPTS):
        try:
            appt = _try_create_walk_in(db, req, now, local, staff)
        except IntegrityError:
            db.rollback()
            if _slot_is_taken(db, req.slot_id):
                raise ReceptionError(
                    409, "SLOT_TAKEN", "Khung giờ vừa có người đặt. Hãy chọn khung khác."
                ) from None
            continue  # trùng mã lịch hoặc số thứ tự: thử lại
        except ReceptionError:
            db.rollback()
            raise
        return _to_out(appt, now, set())
    raise ReceptionError(409, "CONFLICT", "Không tạo được lịch hẹn. Vui lòng thử lại.")


def _try_create_walk_in(
    db: Session, req: WalkInRequest, now: dt.datetime, local: dt.datetime, staff: Staff
) -> Appointment:
    slot = db.scalar(select(Slot).options(joinedload(Slot.doctor)).where(Slot.id == req.slot_id))
    if slot is None:
        raise ReceptionError(404, "SLOT_NOT_FOUND", "Không tìm thấy khung giờ.")
    if slot.slot_date != local.date():
        raise ReceptionError(
            422, "SLOT_NOT_TODAY", "Khách vãng lai chỉ xếp vào khung giờ của hôm nay."
        )
    if dt.datetime.combine(slot.slot_date, slot.start_time) < local:
        raise ReceptionError(409, "SLOT_PASSED", "Khung giờ đã qua. Hãy chọn khung khác.")
    if slot.blocked or not slot.doctor.active:
        raise ReceptionError(409, "SLOT_UNAVAILABLE", "Khung giờ không còn khả dụng.")
    if _slot_is_taken(db, slot.id):
        raise ReceptionError(409, "SLOT_TAKEN", "Khung giờ vừa có người đặt. Hãy chọn khung khác.")

    specialty = _get_specialty(db, slot.doctor.specialty_id)
    profile = _resolve_profile(db, req, local.date())
    _check_specialty_rule(specialty, profile.birth_date, profile.gender, slot.slot_date)
    _check_conflicts(db, profile, slot, specialty.id)

    start = dt.datetime.combine(slot.slot_date, slot.start_time)
    appt = Appointment(
        code=_next_code(db, local.date()),
        profile_id=profile.id,
        specialty_id=specialty.id,
        doctor_id=slot.doctor_id,
        slot_id=slot.id,
        appt_date=slot.slot_date,
        start_time=slot.start_time,
        end_time=(start + dt.timedelta(minutes=SLOT_MINUTES)).time(),
        status=AppointmentStatus.ARRIVED.value,
        channel=Channel.WALK_IN.value,
        created_by=staff.id,
        arrived_at=now,
        checked_in_by=staff.id,
        queue_number=_next_queue_number(db, slot.doctor_id, slot.slot_date),
    )
    appt.profile = profile
    appt.doctor = slot.doctor
    appt.specialty = specialty
    db.add(appt)
    db.commit()
    return appt
