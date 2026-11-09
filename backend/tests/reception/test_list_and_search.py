import datetime as dt

from app.models import AppointmentStatus, Channel
from app.reception import service

from .conftest import NOW, TODAY, at


def _codes(response):
    return [item["code"] for item in response.json()]


def test_list_returns_only_todays_appointments_sorted_by_start_time(
    client, reception_headers, seed
):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    late = seed.appointment(profile, doc, seed.slot(doc, at(10)), code="LH-261109-0002")
    early = seed.appointment(profile, doc, seed.slot(doc, at(8)), code="LH-261109-0001")
    tomorrow = TODAY + dt.timedelta(days=1)
    seed.appointment(profile, doc, seed.slot(doc, at(9), day=tomorrow), code="LH-261110-0001")

    response = client.get("/reception/appointments", headers=reception_headers)

    assert response.status_code == 200
    assert _codes(response) == [early.code, late.code]


def test_list_is_empty_when_no_appointment_today(client, reception_headers):
    response = client.get("/reception/appointments", headers=reception_headers)

    assert response.json() == []


def test_list_uses_clinic_timezone_for_today(client, reception_headers, seed, clock):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    appt = seed.appointment(seed.profile(), doc, seed.slot(doc, at(8)))
    # 20:00 UTC ngày 08/11 = 03:00 ngày 09/11 giờ Việt Nam: vẫn là "hôm nay" của phòng khám.
    clock.now = dt.datetime(2026, 11, 8, 20, 0, tzinfo=dt.UTC)

    response = client.get("/reception/appointments", headers=reception_headers)

    assert _codes(response) == [appt.code]


def test_search_by_appointment_code(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    a = seed.appointment(
        seed.profile(name="Lê Thị Hoa", phone="0911111111"),
        doc,
        seed.slot(doc, at(8)),
        code="LH-261109-0001",
    )
    seed.appointment(
        seed.profile(name="Phạm Văn Bình", phone="0922222222"),
        doc,
        seed.slot(doc, at(9)),
        code="LH-261109-0002",
    )

    response = client.get(
        "/reception/appointments", params={"q": "lh-261109-0001"}, headers=reception_headers
    )

    assert _codes(response) == [a.code]


def test_search_by_phone_matches_partial_digits(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    a = seed.appointment(
        seed.profile(name="Lê Thị Hoa", phone="0911111111"), doc, seed.slot(doc, at(8))
    )
    seed.appointment(
        seed.profile(name="Phạm Văn Bình", phone="0922222222"), doc, seed.slot(doc, at(9))
    )

    response = client.get(
        "/reception/appointments", params={"q": "0911111111"}, headers=reception_headers
    )

    assert _codes(response) == [a.code]


def test_search_by_phone_falls_back_to_account_phone(client, reception_headers, seed, db):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile(name="Trần Bé Na", phone="0933333333")
    profile.phone = None  # hồ sơ người thân không có số: dùng số của tài khoản
    db.commit()
    appt = seed.appointment(profile, doc, seed.slot(doc, at(8)))

    response = client.get(
        "/reception/appointments", params={"q": "0933333333"}, headers=reception_headers
    )

    assert _codes(response) == [appt.code]
    assert response.json()[0]["patient_phone"] == "0933333333"


def test_search_by_name_ignores_case_and_diacritics(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    a = seed.appointment(
        seed.profile(name="Đặng Thị Hồng", phone="0944444444"), doc, seed.slot(doc, at(8))
    )
    seed.appointment(
        seed.profile(name="Phạm Văn Bình", phone="0955555555"), doc, seed.slot(doc, at(9))
    )

    for query in ("dang thi hong", "ĐẶNG", "hong"):
        response = client.get(
            "/reception/appointments", params={"q": query}, headers=reception_headers
        )
        assert _codes(response) == [a.code], query


def test_search_does_not_return_other_days(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile(name="Lê Thị Hoa")
    yesterday = TODAY - dt.timedelta(days=1)
    seed.appointment(profile, doc, seed.slot(doc, at(8), day=yesterday), code="LH-261108-0001")

    response = client.get("/reception/appointments", params={"q": "Hoa"}, headers=reception_headers)

    assert response.json() == []


def test_blank_query_returns_everything_today(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    seed.appointment(seed.profile(), doc, seed.slot(doc, at(8)))

    response = client.get("/reception/appointments", params={"q": "   "}, headers=reception_headers)

    assert len(response.json()) == 1


def test_query_longer_than_100_characters_is_rejected(client, reception_headers):
    response = client.get(
        "/reception/appointments", params={"q": "a" * 101}, headers=reception_headers
    )

    assert response.status_code == 422


def test_filter_by_doctor(client, reception_headers, seed):
    spec = seed.specialty()
    doc_a = seed.doctor(spec, name="Bác sĩ A")
    doc_b = seed.doctor(spec, name="Bác sĩ B")
    profile = seed.profile()
    seed.appointment(profile, doc_a, seed.slot(doc_a, at(8)))
    b = seed.appointment(profile, doc_b, seed.slot(doc_b, at(9)))

    response = client.get(
        "/reception/appointments", params={"doctor_id": doc_b.id}, headers=reception_headers
    )

    assert _codes(response) == [b.code]


def test_filter_by_status(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    seed.appointment(profile, doc, seed.slot(doc, at(8)))
    arrived = seed.appointment(
        profile, doc, seed.slot(doc, at(9)), status=AppointmentStatus.ARRIVED, queue=1
    )

    response = client.get(
        "/reception/appointments", params={"status": "arrived"}, headers=reception_headers
    )

    assert _codes(response) == [arrived.code]


def test_invalid_status_filter_is_rejected(client, reception_headers):
    response = client.get(
        "/reception/appointments", params={"status": "bogus"}, headers=reception_headers
    )

    assert response.status_code == 422


def test_failed_notification_shows_warning_flag(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    failed = seed.appointment(profile, doc, seed.slot(doc, at(8)))
    sent = seed.appointment(profile, doc, seed.slot(doc, at(9)))
    pending = seed.appointment(profile, doc, seed.slot(doc, at(10)))
    seed.notification(failed, "failed")
    seed.notification(sent, "sent")
    seed.notification(pending, "pending")

    flags = {
        item["code"]: item["has_failed_notification"]
        for item in client.get("/reception/appointments", headers=reception_headers).json()
    }

    assert flags == {failed.code: True, sent.code: False, pending.code: False}


def test_item_exposes_patient_doctor_and_channel(client, reception_headers, seed):
    spec = seed.specialty(name="Nhi")
    doc = seed.doctor(spec, name="Trần Thị Lan")
    seed.appointment(
        seed.profile(name="Lê Thị Hoa", phone="0911111111"),
        doc,
        seed.slot(doc, at(8)),
        channel=Channel.ONLINE,
    )

    item = client.get("/reception/appointments", headers=reception_headers).json()[0]

    assert item["patient_name"] == "Lê Thị Hoa"
    assert item["doctor_name"] == "Trần Thị Lan"
    assert item["specialty_name"] == "Nhi"
    assert item["channel"] == "online"
    assert item["status"] == "booked"
    assert item["start_time"] == "08:00:00"
    assert item["end_time"] == "08:15:00"


def test_lookup_lists_return_only_active_items_sorted(client, reception_headers, seed):
    noi = seed.specialty(name="Nội")
    seed.specialty(name="Ngoại ngưng", active=False)
    seed.doctor(noi, name="B bác sĩ")
    seed.doctor(noi, name="A bác sĩ")
    seed.doctor(noi, name="Z nghỉ", active=False)

    specialties = client.get("/reception/specialties", headers=reception_headers).json()
    doctors = client.get("/reception/doctors", headers=reception_headers).json()

    assert [s["name"] for s in specialties] == ["Nội"]
    assert [d["full_name"] for d in doctors] == ["A bác sĩ", "B bác sĩ"]


def test_fold_removes_diacritics_and_normalises_d_stroke():
    assert service.fold("  Đỗ  Thị Ánh ") == "do thi anh"


def test_to_local_keeps_naive_datetime_and_converts_aware_one():
    naive = dt.datetime(2026, 11, 9, 9, 0)

    assert service.to_local(naive) == naive
    assert service.to_local(NOW) == naive
    assert service.to_local(dt.datetime(2026, 11, 9, 2, 0, tzinfo=dt.UTC)) == naive
