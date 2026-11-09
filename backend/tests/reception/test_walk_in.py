import datetime as dt

from sqlalchemy import func, select

from app.models import (
    Appointment,
    AppointmentStatus,
    Channel,
    Notification,
    PatientAccount,
    PatientProfile,
)

from .conftest import TODAY, at

NEW_PROFILE = {
    "full_name": "Nguyễn Văn Khách",
    "birth_date": "1992-03-15",
    "gender": "Nam",
    "phone": "0977000111",
}


def _suggest(client, headers, specialty):
    return client.get(
        "/reception/walk-in/suggestions", params={"specialty_id": specialty.id}, headers=headers
    )


def _walk_in(client, headers, slot, **body):
    return client.post("/reception/walk-in", json={"slot_id": slot.id, **body}, headers=headers)


# ---------- gợi ý khung trống ----------


def test_suggests_earliest_free_slot_per_doctor_sorted_by_time(client, reception_headers, seed):
    spec = seed.specialty()
    doc_a = seed.doctor(spec, name="Bác sĩ A")
    doc_b = seed.doctor(spec, name="Bác sĩ B")
    seed.slot(doc_a, at(10))
    a_early = seed.slot(doc_a, at(9, 15))
    b_first = seed.slot(doc_b, at(9, 0))  # đúng giờ hiện tại 09:00 vẫn được gợi ý
    seed.slot(doc_b, at(9, 30))

    body = _suggest(client, reception_headers, spec).json()

    assert [s["slot_id"] for s in body["suggestions"]] == [b_first.id, a_early.id]
    assert body["message"] is None
    assert body["next_available_date"] is None


def test_suggestion_includes_walk_in_slots(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    walk_in = seed.slot(doc, at(9, 15), kind="walk_in")

    suggestion = _suggest(client, reception_headers, spec).json()["suggestions"][0]

    assert suggestion["slot_id"] == walk_in.id
    assert suggestion["is_walk_in_slot"] is True
    assert suggestion["end_time"] == "09:30:00"


def test_suggestions_skip_past_booked_blocked_and_inactive_doctor_slots(
    client, reception_headers, seed
):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    inactive = seed.doctor(spec, name="Đã nghỉ việc", active=False)
    seed.slot(doc, at(8, 45))  # đã qua
    booked = seed.slot(doc, at(9, 15))
    seed.appointment(seed.profile(), doc, booked)
    seed.slot(doc, at(9, 30), blocked=True)
    seed.slot(inactive, at(9, 15))
    free = seed.slot(doc, at(9, 45))

    body = _suggest(client, reception_headers, spec).json()

    assert [s["slot_id"] for s in body["suggestions"]] == [free.id]


def test_cancelled_appointment_frees_its_slot_for_suggestions(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15))
    seed.appointment(seed.profile(), doc, slot, status=AppointmentStatus.CANCELLED)

    body = _suggest(client, reception_headers, spec).json()

    assert [s["slot_id"] for s in body["suggestions"]] == [slot.id]


def test_suggestions_only_cover_the_chosen_specialty(client, reception_headers, seed):
    noi = seed.specialty(name="Nội")
    nhi = seed.specialty(name="Nhi")
    seed.slot(seed.doctor(nhi, name="Bác sĩ Nhi"), at(9, 15))
    expected = seed.slot(seed.doctor(noi, name="Bác sĩ Nội"), at(9, 30))

    body = _suggest(client, reception_headers, noi).json()

    assert [s["slot_id"] for s in body["suggestions"]] == [expected.id]


def test_sold_out_today_reports_message_and_nearest_available_date(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    seed.slot(doc, at(8, 0))  # đã qua
    seed.slot(doc, at(10), day=TODAY + dt.timedelta(days=3), blocked=True)
    near = TODAY + dt.timedelta(days=2)
    seed.slot(doc, at(14), day=near)
    seed.slot(doc, at(8), day=TODAY + dt.timedelta(days=5))

    body = _suggest(client, reception_headers, spec).json()

    assert body["suggestions"] == []
    assert body["message"] == "Hết chỗ hôm nay"
    assert body["next_available_date"] == near.isoformat()


def test_sold_out_with_no_future_slot_has_no_next_date(client, reception_headers, seed):
    spec = seed.specialty()
    seed.doctor(spec)

    body = _suggest(client, reception_headers, spec).json()

    assert body["message"] == "Hết chỗ hôm nay"
    assert body["next_available_date"] is None


def test_next_available_date_is_limited_to_30_day_window(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    seed.slot(doc, at(9), day=TODAY + dt.timedelta(days=30))  # ngày thứ 31: ngoài giới hạn

    assert _suggest(client, reception_headers, spec).json()["next_available_date"] is None

    last_day = TODAY + dt.timedelta(days=29)  # ngày thứ 30: còn trong giới hạn
    seed.slot(doc, at(9), day=last_day)

    assert _suggest(client, reception_headers, spec).json()["next_available_date"] == str(last_day)


def test_suggestions_for_unknown_or_inactive_specialty_return_404(client, reception_headers, seed):
    inactive = seed.specialty(name="Ngưng", active=False)

    unknown = client.get(
        "/reception/walk-in/suggestions", params={"specialty_id": 999}, headers=reception_headers
    )
    stopped = _suggest(client, reception_headers, inactive)

    assert unknown.status_code == stopped.status_code == 404
    assert unknown.json()["detail"]["code"] == "SPECIALTY_NOT_FOUND"


def test_suggestions_require_specialty_id(client, reception_headers):
    response = client.get("/reception/walk-in/suggestions", headers=reception_headers)

    assert response.status_code == 422


# ---------- tìm hồ sơ ----------


def test_search_profiles_by_account_phone_returns_visible_profiles_primary_first(
    client, reception_headers, seed
):
    primary = seed.profile(name="Chính Chủ", phone="0912345678")
    account = primary.account
    relative = seed.profile(
        name="An Người Thân", phone="0912345678", account=account, primary=False
    )
    seed.profile(name="Đã Ẩn", phone="0912345678", account=account, primary=False, hidden=True)
    seed.profile(name="Người Khác", phone="0999999999")

    response = client.get(
        "/reception/profiles", params={"phone": "0912345678"}, headers=reception_headers
    )

    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [primary.id, relative.id]
    assert response.json()[0]["is_primary"] is True


def test_search_profiles_without_match_returns_empty_list(client, reception_headers):
    response = client.get(
        "/reception/profiles", params={"phone": "0900000000"}, headers=reception_headers
    )

    assert response.status_code == 200
    assert response.json() == []


def test_search_profiles_rejects_invalid_phone(client, reception_headers):
    for phone in ("12345", "1912345678", "091234567", "09123456789", "09123abcde"):
        response = client.get(
            "/reception/profiles", params={"phone": phone}, headers=reception_headers
        )
        assert response.status_code == 422, phone
        assert response.json()["detail"]["code"] == "INVALID_PHONE"


# ---------- tạo lịch vãng lai ----------


def test_walk_in_with_existing_profile_creates_arrived_walk_in_appointment(
    client, reception_headers, seed, db
):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15), kind="walk_in")
    profile = seed.profile()

    response = _walk_in(client, reception_headers, slot, profile_id=profile.id)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "arrived"
    assert body["channel"] == "walk_in"
    assert body["queue_number"] == 1
    assert body["code"] == "LH-261109-0001"
    assert body["doctor_name"] == doc.full_name
    appt = db.scalar(select(Appointment))
    assert appt.created_by == 1
    assert appt.checked_in_by == 1
    assert appt.arrived_at is not None
    assert appt.slot_id == slot.id
    assert appt.end_time == at(9, 30)


def test_walk_in_does_not_create_any_notification(client, reception_headers, seed, db):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15))

    _walk_in(client, reception_headers, slot, profile_id=seed.profile().id)

    assert db.scalar(select(func.count()).select_from(Notification)) == 0


def test_walk_in_with_new_profile_creates_account_and_primary_profile(
    client, reception_headers, seed, db
):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    response = _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE)

    assert response.status_code == 201
    assert response.json()["patient_name"] == "Nguyễn Văn Khách"
    account = db.scalar(select(PatientAccount).where(PatientAccount.phone == "0977000111"))
    profile = db.scalar(select(PatientProfile))
    assert account is not None
    assert profile.is_primary is True
    assert profile.account_id == account.id


def test_walk_in_new_profile_reuses_existing_account_and_same_person(
    client, reception_headers, seed, db
):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    existing = seed.profile(name="Nguyễn Văn Khách", phone="0977000111", birth=dt.date(1992, 3, 15))
    slot = seed.slot(doc, at(9, 15))

    response = _walk_in(
        client,
        reception_headers,
        slot,
        new_profile={**NEW_PROFILE, "full_name": "nguyen van khach"},
    )

    assert response.status_code == 201
    assert db.scalar(select(func.count()).select_from(PatientProfile)) == 1
    assert db.scalar(select(Appointment)).profile_id == existing.id


def test_walk_in_new_profile_of_second_person_on_same_phone_is_not_primary(
    client, reception_headers, seed, db
):
    spec = seed.specialty()
    seed.profile(name="Chính Chủ", phone="0977000111")
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    response = _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE)

    assert response.status_code == 201
    created = db.scalar(select(PatientProfile).where(PatientProfile.full_name.like("%Khách")))
    assert created.is_primary is False


def test_walk_in_new_profile_blocked_when_account_has_five_visible_profiles(
    client, reception_headers, seed
):
    spec = seed.specialty()
    first = seed.profile(name="Hồ Sơ Một", phone="0977000111")
    for index, name in enumerate(["Hai", "Ba", "Bốn", "Năm"], start=2):
        seed.profile(
            name=f"Hồ Sơ {name}",
            phone="0977000111",
            account=first.account,
            primary=False,
            birth=dt.date(1980 + index, 1, 1),
        )
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    response = _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PROFILE_LIMIT_REACHED"


def test_walk_in_hidden_profiles_do_not_count_toward_limit(client, reception_headers, seed):
    spec = seed.specialty()
    first = seed.profile(name="Hồ Sơ Một", phone="0977000111")
    for index in range(5):
        seed.profile(
            name=f"Ẩn {chr(65 + index)}",
            phone="0977000111",
            account=first.account,
            primary=False,
            hidden=True,
        )
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    assert _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE).status_code == 201


def test_appointment_codes_increase_within_the_day(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    first_slot = seed.slot(doc, at(9, 15))
    second_slot = seed.slot(doc, at(9, 30))
    other_day = TODAY + dt.timedelta(days=1)
    seed.appointment(
        seed.profile(name="Hẹn Mai", phone="0900000001"),
        doc,
        seed.slot(doc, at(9), day=other_day),
        code="LH-261109-0007",  # mã tạo trong ngày hôm nay cho lịch ngày mai
    )

    one = _walk_in(client, reception_headers, first_slot, new_profile=NEW_PROFILE)
    two = _walk_in(
        client,
        reception_headers,
        second_slot,
        new_profile={**NEW_PROFILE, "full_name": "Trần Thị Hai", "phone": "0977000222"},
    )

    assert one.json()["code"] == "LH-261109-0008"
    assert two.json()["code"] == "LH-261109-0009"


def test_walk_in_queue_number_continues_per_doctor(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    seed.appointment(
        seed.profile(name="Đã Đến", phone="0900000002"),
        doc,
        seed.slot(doc, at(9, 0)),
        status=AppointmentStatus.ARRIVED,
        queue=1,
    )
    slot = seed.slot(doc, at(9, 15))

    response = _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE)

    assert response.json()["queue_number"] == 2


def test_walk_in_slot_already_booked_returns_409(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15))
    seed.appointment(seed.profile(name="Người Trước", phone="0900000003"), doc, slot)
    other = seed.profile(name="Người Sau", phone="0900000004")

    response = _walk_in(client, reception_headers, slot, profile_id=other.id)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SLOT_TAKEN"


def test_walk_in_slot_can_be_reused_after_cancellation(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15))
    seed.appointment(
        seed.profile(name="Người Trước", phone="0900000003"),
        doc,
        slot,
        status=AppointmentStatus.CANCELLED,
    )
    other = seed.profile(name="Người Sau", phone="0900000004")

    assert _walk_in(client, reception_headers, slot, profile_id=other.id).status_code == 201


def test_walk_in_maps_database_conflict_to_slot_taken(seed, db, monkeypatch):
    """Hai lễ tân cùng chọn một khung: chỉ một lịch được tạo, người còn lại nhận SLOT_TAKEN."""
    import pytest

    from app import auth
    from app.reception import schemas, service
    from app.reception.errors import ReceptionError

    from .conftest import NOW

    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15))
    loser = seed.profile(name="Người Thua", phone="0900000004")
    winner = seed.profile(name="Người Thắng", phone="0900000005")
    real = service._slot_is_taken
    checks = []

    def racing(session, slot_id):
        checks.append(1)
        if len(checks) == 1:
            return False  # lúc kiểm tra thì còn trống
        return real(session, slot_id)

    monkeypatch.setattr(service, "_slot_is_taken", racing)
    seed.appointment(winner, doc, slot)  # ...nhưng người kia đã chèn lịch trước khi commit

    with pytest.raises(ReceptionError) as excinfo:
        service.create_walk_in(
            db,
            schemas.WalkInRequest(slot_id=slot.id, profile_id=loser.id),
            NOW,
            auth.Staff(id=1, role="receptionist"),
        )

    assert excinfo.value.code == "SLOT_TAKEN"
    assert db.scalar(select(func.count()).select_from(Appointment)) == 1


def test_walk_in_unknown_slot_returns_404(client, reception_headers, seed):
    profile = seed.profile()

    response = client.post(
        "/reception/walk-in",
        json={"slot_id": 999, "profile_id": profile.id},
        headers=reception_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "SLOT_NOT_FOUND"


def test_walk_in_unknown_profile_returns_404(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    response = _walk_in(client, reception_headers, slot, profile_id=999)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


def test_walk_in_hidden_profile_is_not_usable(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))
    hidden = seed.profile(hidden=True)

    response = _walk_in(client, reception_headers, slot, profile_id=hidden.id)

    assert response.status_code == 404


def test_walk_in_rejects_slot_of_another_day(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15), day=TODAY + dt.timedelta(days=1))

    response = _walk_in(client, reception_headers, slot, profile_id=seed.profile().id)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "SLOT_NOT_TODAY"


def test_walk_in_rejects_slot_in_the_past(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(8, 45))

    response = _walk_in(client, reception_headers, slot, profile_id=seed.profile().id)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SLOT_PASSED"


def test_walk_in_rejects_blocked_slot_and_inactive_doctor(client, reception_headers, seed):
    spec = seed.specialty()
    profile = seed.profile()
    blocked = seed.slot(seed.doctor(spec), at(9, 15), blocked=True)
    inactive_slot = seed.slot(seed.doctor(spec, name="Đã nghỉ", active=False), at(9, 15))

    for slot in (blocked, inactive_slot):
        response = _walk_in(client, reception_headers, slot, profile_id=profile.id)
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "SLOT_UNAVAILABLE"


def test_walk_in_body_requires_exactly_one_profile_source(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))
    profile = seed.profile()

    neither = _walk_in(client, reception_headers, slot)
    both = _walk_in(client, reception_headers, slot, profile_id=profile.id, new_profile=NEW_PROFILE)

    assert neither.status_code == both.status_code == 422


def test_failed_walk_in_leaves_no_profile_or_appointment_behind(
    client, reception_headers, seed, db
):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    slot = seed.slot(doc, at(9, 15))
    seed.appointment(seed.profile(name="Người Trước", phone="0900000003"), doc, slot)

    response = _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE)

    assert response.status_code == 409
    assert db.scalar(select(func.count()).select_from(PatientProfile)) == 1
    assert db.scalar(select(func.count()).select_from(Appointment)) == 1


def test_walk_in_works_in_the_early_morning_after_midnight_utc(
    client, reception_headers, seed, clock
):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(7, 30))
    # 00:10 UTC = 07:10 giờ Việt Nam cùng ngày 09/11.
    clock.now = dt.datetime(2026, 11, 9, 0, 10, tzinfo=dt.UTC)

    response = _walk_in(client, reception_headers, slot, profile_id=seed.profile().id)

    assert response.status_code == 201
    assert response.json()["code"] == "LH-261109-0001"


# ---------- BR-LK-06 và BR-LK-02 ----------


def test_pediatrics_rejects_profile_aged_16_on_the_visit_day(client, reception_headers, seed):
    nhi = seed.specialty(name="Nhi", max_age=16)
    slot = seed.slot(seed.doctor(nhi), at(9, 15))
    sixteen = seed.profile(birth=dt.date(2010, 11, 9))  # đúng 16 tuổi hôm nay

    response = _walk_in(client, reception_headers, slot, profile_id=sixteen.id)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SPECIALTY_AGE_RESTRICTED"


def test_pediatrics_accepts_profile_one_day_before_16th_birthday(client, reception_headers, seed):
    nhi = seed.specialty(name="Nhi", max_age=16)
    slot = seed.slot(seed.doctor(nhi), at(9, 15))
    fifteen = seed.profile(birth=dt.date(2010, 11, 10))

    assert _walk_in(client, reception_headers, slot, profile_id=fifteen.id).status_code == 201


def test_obstetrics_rejects_male_profile_and_accepts_female(client, reception_headers, seed):
    san = seed.specialty(name="Sản phụ khoa", gender="Nữ")
    doc = seed.doctor(san)
    male = seed.profile(name="Nam Giới", phone="0900000010", gender="Nam")
    female = seed.profile(name="Nữ Giới", phone="0900000011", gender="Nữ")

    rejected = _walk_in(client, reception_headers, seed.slot(doc, at(9, 15)), profile_id=male.id)
    accepted = _walk_in(client, reception_headers, seed.slot(doc, at(9, 30)), profile_id=female.id)

    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "SPECIALTY_GENDER_RESTRICTED"
    assert accepted.status_code == 201


def test_walk_in_rejects_same_day_same_specialty_duplicate(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    seed.appointment(profile, doc, seed.slot(doc, at(14)))

    response = _walk_in(client, reception_headers, seed.slot(doc, at(9, 15)), profile_id=profile.id)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "DUPLICATE_SAME_DAY_SPECIALTY"


def test_cancelled_appointment_does_not_block_same_specialty_walk_in(
    client, reception_headers, seed
):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    seed.appointment(profile, doc, seed.slot(doc, at(14)), status=AppointmentStatus.CANCELLED)

    response = _walk_in(client, reception_headers, seed.slot(doc, at(9, 15)), profile_id=profile.id)

    assert response.status_code == 201


def test_walk_in_rejects_overlapping_appointment_of_another_specialty(
    client, reception_headers, seed
):
    noi = seed.specialty(name="Nội")
    mat = seed.specialty(name="Mắt")
    doc_noi = seed.doctor(noi, name="Bác sĩ Nội")
    doc_mat = seed.doctor(mat, name="Bác sĩ Mắt")
    profile = seed.profile()
    seed.appointment(profile, doc_noi, seed.slot(doc_noi, at(9, 15)))

    response = _walk_in(
        client, reception_headers, seed.slot(doc_mat, at(9, 15)), profile_id=profile.id
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "OVERLAPPING_APPOINTMENT"


def test_walk_in_accepts_adjacent_non_overlapping_other_specialty(client, reception_headers, seed):
    noi = seed.specialty(name="Nội")
    mat = seed.specialty(name="Mắt")
    doc_noi = seed.doctor(noi, name="Bác sĩ Nội")
    doc_mat = seed.doctor(mat, name="Bác sĩ Mắt")
    profile = seed.profile()
    seed.appointment(profile, doc_noi, seed.slot(doc_noi, at(9, 0)))

    response = _walk_in(
        client, reception_headers, seed.slot(doc_mat, at(9, 15)), profile_id=profile.id
    )

    assert response.status_code == 201


def test_walk_in_status_of_created_appointment_is_never_booked(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    response = _walk_in(client, reception_headers, slot, new_profile=NEW_PROFILE)

    assert response.json()["status"] == AppointmentStatus.ARRIVED.value
    assert response.json()["channel"] == Channel.WALK_IN.value


def test_walk_in_new_profile_with_future_birth_date_returns_422(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))
    future = (TODAY + dt.timedelta(days=1)).isoformat()

    response = _walk_in(
        client, reception_headers, slot, new_profile={**NEW_PROFILE, "birth_date": future}
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "BIRTH_DATE_IN_FUTURE"


def test_walk_in_accepts_new_profile_born_today(client, reception_headers, seed):
    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))

    response = _walk_in(
        client,
        reception_headers,
        slot,
        new_profile={**NEW_PROFILE, "birth_date": TODAY.isoformat()},
    )

    assert response.status_code == 201


def test_walk_in_retries_after_code_collision_then_succeeds(seed, db, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    from app import auth
    from app.reception import schemas, service

    from .conftest import NOW

    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))
    profile = seed.profile()
    real = service._try_create_walk_in
    calls = []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise IntegrityError("insert", {}, Exception("duplicate code"))
        return real(*args, **kwargs)

    monkeypatch.setattr(service, "_try_create_walk_in", flaky)

    result = service.create_walk_in(
        db,
        schemas.WalkInRequest(slot_id=slot.id, profile_id=profile.id),
        NOW,
        auth.Staff(id=1, role="receptionist"),
    )

    assert len(calls) == 2
    assert result.status == AppointmentStatus.ARRIVED.value


def test_walk_in_gives_up_with_conflict_after_max_attempts(seed, db, monkeypatch):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from app import auth
    from app.reception import schemas, service
    from app.reception.errors import ReceptionError

    from .conftest import NOW

    spec = seed.specialty()
    slot = seed.slot(seed.doctor(spec), at(9, 15))
    profile = seed.profile()
    calls = []

    def always_fails(*args, **kwargs):
        calls.append(1)
        raise IntegrityError("insert", {}, Exception("duplicate code"))

    monkeypatch.setattr(service, "_try_create_walk_in", always_fails)

    with pytest.raises(ReceptionError) as excinfo:
        service.create_walk_in(
            db,
            schemas.WalkInRequest(slot_id=slot.id, profile_id=profile.id),
            NOW,
            auth.Staff(id=1, role="receptionist"),
        )

    assert excinfo.value.status_code == 409
    assert excinfo.value.code == "CONFLICT"
    assert len(calls) == service._MAX_ATTEMPTS
