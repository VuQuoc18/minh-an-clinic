import datetime as dt

from sqlalchemy import select

from app.models import LoginThrottle, PatientAccount, PatientSession
from app.modules.auth.service import LOCK_DURATION, MAX_FAILED_ATTEMPTS

from .conftest import NOW, PASSWORD, PHONE

URL = "/api/auth/patient/login"


def _login(client, phone=PHONE, password=PASSWORD):
    return client.post(URL, json={"so_dien_thoai": phone, "mat_khau": password})


def _throttle(db, phone=PHONE):
    db.expire_all()
    return db.scalar(select(LoginThrottle).where(LoginThrottle.phone == phone))


def _fail(client, times, phone=PHONE):
    return [_login(client, phone, "sai-mat-khau") for _ in range(times)]


# ---------- đăng nhập thành công ----------


def test_login_without_primary_profile_flags_profile_form(client, seed):
    seed.account()

    resp = _login(client)

    assert resp.status_code == 200
    body = resp.json()
    assert body["ket_qua"] == "THANH_CONG"
    assert body["can_tao_ho_so"] is True
    assert body["so_dien_thoai"] == PHONE
    assert body["token"]


def test_login_with_primary_profile_goes_to_my_appointments(client, seed):
    seed.profile(seed.account())

    body = _login(client).json()

    assert body["ket_qua"] == "THANH_CONG"
    assert body["can_tao_ho_so"] is False


def test_hidden_primary_profile_does_not_count(client, seed):
    seed.profile(seed.account(), hidden=True)

    assert _login(client).json()["can_tao_ho_so"] is True


def test_non_primary_profile_does_not_count(client, seed):
    seed.profile(seed.account(), primary=False)

    assert _login(client).json()["can_tao_ho_so"] is True


def test_login_creates_session_with_hashed_token_and_30_day_expiry(client, seed, db, clock):
    account = seed.account()

    body = _login(client).json()

    session = db.scalars(select(PatientSession)).one()
    assert session.account_id == account.id
    assert session.status == "active"
    assert session.token_hash != body["token"]
    assert len(session.token_hash) == 64
    assert dt.datetime.fromisoformat(body["het_han_luc"]) == clock.now + dt.timedelta(days=30)


def test_each_login_gets_a_different_token(client, seed):
    seed.account()

    assert _login(client).json()["token"] != _login(client).json()["token"]


def test_successful_login_resets_failed_counter(client, seed, db):
    seed.account()
    _fail(client, 3)
    assert _throttle(db).failed_count == 3

    assert _login(client).status_code == 200

    assert _throttle(db).failed_count == 0
    assert _fail(client, 1)[0].json()["detail"]["so_lan_con_lai"] == MAX_FAILED_ATTEMPTS - 1


# ---------- chưa có mật khẩu ----------


def test_unknown_phone_returns_no_password_result(client, db):
    resp = _login(client)

    assert resp.status_code == 200
    assert resp.json() == {
        "ket_qua": "CHUA_CO_MAT_KHAU",
        "so_dien_thoai": PHONE,
        "token": None,
        "het_han_luc": None,
        "can_tao_ho_so": False,
    }
    assert db.scalars(select(PatientSession)).all() == []


def test_account_without_password_returns_no_password_result(client, seed):
    seed.account(password=None)

    assert _login(client).json()["ket_qua"] == "CHUA_CO_MAT_KHAU"


def test_account_with_empty_hash_returns_no_password_result(client, seed, db):
    account = seed.account()
    account.password_hash = ""
    db.commit()

    assert _login(client).json()["ket_qua"] == "CHUA_CO_MAT_KHAU"


def test_no_password_result_does_not_touch_failed_counter(client, seed, db):
    seed.account(password=None)

    _login(client)
    _login(client, "0900000000")

    assert db.scalars(select(LoginThrottle)).all() == []


# ---------- sai mật khẩu và khóa (BR-TK-03) ----------


def test_wrong_password_reports_remaining_attempts(client, seed, db):
    seed.account()

    resp = _login(client, password="sai-mat-khau")

    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["code"] == "SAI_THONG_TIN"
    assert detail["so_lan_con_lai"] == 4
    assert "Số điện thoại hoặc mật khẩu không đúng" in detail["message"]
    assert _throttle(db).failed_count == 1
    assert db.scalars(select(PatientSession)).all() == []


def test_remaining_attempts_count_down_to_one(client, seed):
    seed.account()

    remaining = [r.json()["detail"]["so_lan_con_lai"] for r in _fail(client, 4)]

    assert remaining == [4, 3, 2, 1]


def test_fifth_consecutive_wrong_password_locks_for_15_minutes(client, seed, db, clock):
    seed.account()

    resp = _fail(client, 5)[-1]

    assert resp.status_code == 429
    detail = resp.json()["detail"]
    assert detail["code"] == "BI_KHOA"
    retry_at = clock.now + LOCK_DURATION
    assert dt.datetime.fromisoformat(detail["thu_lai_luc"]) == retry_at
    assert "09:15" in detail["message"]
    assert "24/11/2026" in detail["message"]
    assert _throttle(db).failed_count == 5


def test_locked_phone_is_rejected_even_with_correct_password(client, seed, db):
    seed.account()
    _fail(client, 5)

    resp = _login(client)

    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "BI_KHOA"
    assert db.scalars(select(PatientSession)).all() == []


def test_locked_phone_does_not_increase_counter(client, seed, db):
    seed.account()
    _fail(client, 5)

    _fail(client, 3)

    assert _throttle(db).failed_count == 5


def test_lock_is_still_active_one_second_before_expiry(client, seed, clock):
    seed.account()
    _fail(client, 5)
    clock.now += LOCK_DURATION - dt.timedelta(seconds=1)

    assert _login(client).status_code == 429


def test_lock_ends_exactly_after_15_minutes_and_counter_resets(client, seed, db, clock):
    seed.account()
    _fail(client, 5)
    clock.now += LOCK_DURATION

    assert _login(client).status_code == 200

    throttle = _throttle(db)
    assert throttle.failed_count == 0
    assert throttle.locked_until is None


def test_after_lock_expires_wrong_password_starts_counting_from_zero(client, seed, clock):
    seed.account()
    _fail(client, 5)
    clock.now += LOCK_DURATION + dt.timedelta(minutes=1)

    resp = _login(client, password="sai-mat-khau")

    assert resp.status_code == 401
    assert resp.json()["detail"]["so_lan_con_lai"] == 4


def test_lock_applies_per_phone_only(client, seed):
    seed.account()
    seed.account(phone="0987654321")
    _fail(client, 5)

    assert _login(client, "0987654321").status_code == 200


def test_locked_phone_is_checked_before_account_lookup(client, seed, db, clock):
    # Số bị khóa (đã có bộ đếm) trả BI_KHOA dù tài khoản không còn mật khẩu.
    account = seed.account()
    _fail(client, 5)
    account.password_hash = None
    db.commit()

    assert _login(client).json()["detail"]["code"] == "BI_KHOA"


# ---------- dữ liệu không hợp lệ ----------


def test_invalid_phone_returns_422_with_field_error(client):
    resp = client.post(URL, json={"so_dien_thoai": "12345", "mat_khau": "x"})

    assert resp.status_code == 422
    body = resp.json()["detail"]
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["field"] == "so_dien_thoai"


def test_invalid_phone_does_not_touch_database(client, db):
    client.post(URL, json={"so_dien_thoai": "12345", "mat_khau": "x"})

    assert db.scalars(select(LoginThrottle)).all() == []


def test_empty_password_returns_422(client):
    resp = client.post(URL, json={"so_dien_thoai": PHONE, "mat_khau": ""})

    assert resp.status_code == 422
    assert resp.json()["detail"]["errors"][0]["field"] == "mat_khau"


def test_missing_fields_return_422(client):
    assert client.post(URL, json={}).status_code == 422


def test_staff_phone_or_email_is_not_looked_up(client):
    # Trang này không nhận tài khoản nhân viên: email không qua được kiểm tra định dạng.
    resp = client.post(URL, json={"so_dien_thoai": "le.tan@minhan.example", "mat_khau": "x"})

    assert resp.status_code == 422


# ---------- lỗi hệ thống ----------


def test_system_error_rolls_back_and_keeps_counter(client, seed, db, monkeypatch):
    seed.account()
    _fail(client, 2)

    from app.modules.auth import service

    def boom(*_args, **_kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(service, "_create_session", boom)
    failing = type(client)(client.app, raise_server_exceptions=False)
    assert failing.post(URL, json={"so_dien_thoai": PHONE, "mat_khau": PASSWORD}).status_code == 500

    assert _throttle(db).failed_count == 2


def test_first_wrong_password_creates_throttle_row_once(client, seed, db):
    seed.account()

    _fail(client, 1)

    rows = db.scalars(select(LoginThrottle)).all()
    assert [(r.phone, r.failed_count) for r in rows] == [(PHONE, 1)]


def test_throttle_row_created_by_parallel_request_is_reused(client, seed, db, monkeypatch):
    """Request song song tạo dòng sau khi request này đã đọc (chưa có dòng): không tạo trùng."""
    from app.modules.auth import service

    seed.account()
    real_verify = service.verify_password

    def verify_after_parallel_insert(password, password_hash):
        db.add(LoginThrottle(phone=PHONE, failed_count=3))
        db.commit()
        return real_verify(password, password_hash)

    monkeypatch.setattr(service, "verify_password", verify_after_parallel_insert)

    body = client.post(URL, json={"so_dien_thoai": PHONE, "mat_khau": "sai-mat-khau"}).json()

    assert body["detail"]["so_lan_con_lai"] == 1
    rows = db.scalars(select(LoginThrottle)).all()
    assert [r.failed_count for r in rows] == [4]


def test_parallel_request_that_locked_the_phone_stops_this_attempt(client, seed, db, monkeypatch):
    from app.modules.auth import service

    seed.account()
    real_verify = service.verify_password
    until = NOW + LOCK_DURATION

    def verify_after_parallel_lock(password, password_hash):
        db.add(LoginThrottle(phone=PHONE, failed_count=MAX_FAILED_ATTEMPTS, locked_until=until))
        db.commit()
        return real_verify(password, password_hash)

    monkeypatch.setattr(service, "verify_password", verify_after_parallel_lock)

    response = client.post(URL, json={"so_dien_thoai": PHONE, "mat_khau": "sai-mat-khau"})

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "BI_KHOA"
    assert _throttle(db).failed_count == MAX_FAILED_ATTEMPTS


def test_account_is_not_modified_by_login(client, seed, db):
    account = seed.account()
    before = account.password_hash

    _login(client)

    db.expire_all()
    assert db.get(PatientAccount, account.id).password_hash == before


def test_naive_datetime_from_database_is_handled(client, seed, db, clock):
    # SQLite trả thời điểm khóa không kèm múi giờ; vẫn so sánh đúng.
    seed.account()
    db.add(LoginThrottle(phone=PHONE, failed_count=5, locked_until=(clock.now + LOCK_DURATION)))
    db.commit()

    assert _login(client).status_code == 429
