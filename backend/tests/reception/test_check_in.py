import datetime as dt

import pytest

from app.models import Appointment, AppointmentStatus

from .conftest import NOW, TODAY, TZ, at


def _setup(seed, start=None, status=AppointmentStatus.BOOKED):
    start = start or at(10)
    spec = seed.specialty()
    doc = seed.doctor(spec)
    appt = seed.appointment(seed.profile(), doc, seed.slot(doc, start), status=status)
    return doc, appt


def _post(client, headers, appt):
    return client.post(f"/reception/appointments/{appt.id}/check-in", headers=headers)


def _set_now(clock, hour, minute=0, second=0):
    clock.now = dt.datetime(2026, 11, 9, hour, minute, second, tzinfo=TZ)


def test_check_in_success_sets_arrived_and_first_queue_number(client, reception_headers, seed, db):
    _, appt = _setup(seed, start=at(9, 30))

    response = _post(client, reception_headers, appt)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "arrived"
    assert body["queue_number"] == 1
    assert body["can_check_in"] is False
    db.refresh(appt)
    assert appt.status == "arrived"
    assert appt.checked_in_by == 1
    assert appt.arrived_at is not None


def test_check_in_by_admin_records_admin_id(client, admin_headers, seed, db):
    _, appt = _setup(seed, start=at(9, 30))

    assert _post(client, admin_headers, appt).status_code == 200
    db.refresh(appt)
    assert appt.checked_in_by == 2


@pytest.mark.parametrize(
    ("hour", "minute", "second", "allowed"),
    [
        (8, 59, 59, False),  # trước mốc -60 phút một giây (giờ hẹn 10:00)
        (9, 0, 0, True),  # đúng -60 phút: biên đóng
        (10, 0, 0, True),  # đúng giờ hẹn
        (10, 15, 0, True),  # đúng +15 phút: biên đóng
        (10, 15, 1, False),  # quá +15 phút một giây
    ],
)
def test_check_in_window_boundaries_of_br_td_01(
    client, reception_headers, seed, clock, hour, minute, second, allowed
):
    _, appt = _setup(seed, start=at(10))
    _set_now(clock, hour, minute, second)

    response = _post(client, reception_headers, appt)

    assert (response.status_code == 200) is allowed
    if not allowed:
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "OUTSIDE_CHECK_IN_WINDOW"


def test_check_in_too_early_message_tells_when_it_opens(client, reception_headers, seed):
    _, appt = _setup(seed, start=at(11))  # bây giờ 09:00, mở lúc 10:00

    response = _post(client, reception_headers, appt)

    assert response.status_code == 409
    assert "10:00" in response.json()["detail"]["message"]


def test_check_in_too_late_message_suggests_walk_in(client, reception_headers, seed, clock):
    _, appt = _setup(seed, start=at(8))
    _set_now(clock, 8, 30)

    response = _post(client, reception_headers, appt)

    assert response.status_code == 409
    message = response.json()["detail"]["message"]
    assert "08:15" in message
    assert "khách vãng lai" in message


def test_failed_check_in_does_not_change_the_appointment(client, reception_headers, seed, db):
    _, appt = _setup(seed, start=at(15))

    _post(client, reception_headers, appt)
    db.refresh(appt)

    assert appt.status == "booked"
    assert appt.queue_number is None


def test_check_in_unknown_appointment_returns_404(client, reception_headers):
    response = client.post("/reception/appointments/999/check-in", headers=reception_headers)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "APPOINTMENT_NOT_FOUND"


@pytest.mark.parametrize(
    "status",
    [
        AppointmentStatus.ARRIVED,
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    ],
)
def test_check_in_requires_booked_status(client, reception_headers, seed, status):
    _, appt = _setup(seed, start=at(9, 30), status=status)

    response = _post(client, reception_headers, appt)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "INVALID_STATUS"


def test_checking_in_twice_is_rejected(client, reception_headers, seed):
    _, appt = _setup(seed, start=at(9, 30))

    assert _post(client, reception_headers, appt).status_code == 200
    second = _post(client, reception_headers, appt)

    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "INVALID_STATUS"


def test_queue_numbers_are_per_doctor_per_day_starting_at_one(client, reception_headers, seed):
    spec = seed.specialty()
    doc_a = seed.doctor(spec, name="Bác sĩ A")
    doc_b = seed.doctor(spec, name="Bác sĩ B")
    profile = seed.profile()
    a1 = seed.appointment(profile, doc_a, seed.slot(doc_a, at(9, 30)))
    a2 = seed.appointment(profile, doc_a, seed.slot(doc_a, at(9, 45)))
    b1 = seed.appointment(profile, doc_b, seed.slot(doc_b, at(9, 30)))

    numbers = [
        _post(client, reception_headers, appt).json()["queue_number"] for appt in (a1, a2, b1)
    ]

    assert numbers == [1, 2, 1]


def test_queue_number_follows_check_in_order_not_start_time(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    earlier = seed.appointment(profile, doc, seed.slot(doc, at(9, 15)))
    later = seed.appointment(profile, doc, seed.slot(doc, at(9, 30)))

    first = _post(client, reception_headers, later).json()["queue_number"]
    second = _post(client, reception_headers, earlier).json()["queue_number"]

    assert (first, second) == (1, 2)


def test_queue_number_ignores_other_days(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    yesterday = TODAY - dt.timedelta(days=1)
    seed.appointment(
        profile,
        doc,
        seed.slot(doc, at(9), day=yesterday),
        status=AppointmentStatus.COMPLETED,
        queue=7,
    )
    today_appt = seed.appointment(profile, doc, seed.slot(doc, at(9, 30)))

    assert _post(client, reception_headers, today_appt).json()["queue_number"] == 1


def test_check_in_retries_when_queue_number_is_taken_concurrently(seed, db, monkeypatch):
    """Hai lễ tân cùng bấm: lần cấp số đầu trùng thì cấp lại số kế tiếp."""
    from app import auth
    from app.reception import service

    _, appt = _setup(seed, start=at(9, 30))
    seed.appointment(  # người kia đã lấy số 1 của cùng bác sĩ, cùng ngày
        seed.profile(name="Người khác", phone="0966666666"),
        appt.doctor,
        seed.slot(appt.doctor, at(9, 45)),
        status=AppointmentStatus.ARRIVED,
        queue=1,
    )
    calls = []
    real = service._next_queue_number

    def stale_then_real(session, doctor_id, day):
        calls.append(1)
        return 1 if len(calls) == 1 else real(session, doctor_id, day)

    monkeypatch.setattr(service, "_next_queue_number", stale_then_real)

    result = service.check_in(db, appt.id, NOW, auth.Staff(id=1, role="receptionist"))

    assert result.queue_number == 2
    assert result.status == "arrived"
    assert len(calls) == 2


def test_check_in_gives_up_after_repeated_queue_conflicts(seed, db, monkeypatch):
    from app import auth
    from app.reception import service
    from app.reception.errors import ReceptionError

    _, appt = _setup(seed, start=at(9, 30))
    seed.appointment(
        seed.profile(name="Người khác", phone="0966666666"),
        appt.doctor,
        seed.slot(appt.doctor, at(9, 45)),
        status=AppointmentStatus.ARRIVED,
        queue=1,
    )
    monkeypatch.setattr(service, "_next_queue_number", lambda *_: 1)

    with pytest.raises(ReceptionError) as excinfo:
        service.check_in(db, appt.id, NOW, auth.Staff(id=1, role="receptionist"))

    assert excinfo.value.status_code == 409
    assert excinfo.value.code == "QUEUE_CONFLICT"
    assert db.get(Appointment, appt.id).status == "booked"


def test_list_item_reports_check_in_state_and_reason(client, reception_headers, seed):
    spec = seed.specialty()
    doc = seed.doctor(spec)
    profile = seed.profile()
    open_now = seed.appointment(profile, doc, seed.slot(doc, at(9, 30)))
    too_early = seed.appointment(profile, doc, seed.slot(doc, at(14)))
    arrived = seed.appointment(
        profile, doc, seed.slot(doc, at(9)), status=AppointmentStatus.ARRIVED, queue=1
    )

    items = {
        item["code"]: item
        for item in client.get("/reception/appointments", headers=reception_headers).json()
    }

    assert items[open_now.code]["can_check_in"] is True
    assert items[open_now.code]["check_in_block_reason"] is None
    assert items[too_early.code]["can_check_in"] is False
    assert "13:00" in items[too_early.code]["check_in_block_reason"]
    assert items[arrived.code]["can_check_in"] is False
    assert items[arrived.code]["check_in_block_reason"] == "Lịch hẹn không ở trạng thái Đã đặt."
    assert items[arrived.code]["queue_number"] == 1


def test_now_dependency_returns_clinic_timezone_time():
    from app.clock import get_now

    now = get_now()

    assert now.tzinfo is not None
    assert now.utcoffset() == dt.timedelta(hours=7)
    assert NOW.utcoffset() == dt.timedelta(hours=7)
