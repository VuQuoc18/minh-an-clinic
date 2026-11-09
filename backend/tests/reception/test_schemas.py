import datetime as dt

import pytest
from pydantic import ValidationError

from app.reception.schemas import NewProfile, WalkInRequest

VALID = {
    "full_name": "Nguyễn Văn An",
    "birth_date": dt.date(1990, 5, 20),
    "gender": "Nam",
    "phone": "0912345678",
}


def make(**overrides):
    return NewProfile(**{**VALID, **overrides})


def test_valid_profile_is_accepted_and_name_is_trimmed():
    profile = make(full_name="  Nguyễn Văn An  ")

    assert profile.full_name == "Nguyễn Văn An"
    assert profile.email is None
    assert profile.address is None


@pytest.mark.parametrize("name", ["A", "", " ", "A" * 101, "An 2", "An@", "An-Binh", "An_B"])
def test_invalid_names_are_rejected(name):
    with pytest.raises(ValidationError):
        make(full_name=name)


@pytest.mark.parametrize("name", ["An", "A" * 100, "Đặng Thị Hồng Nhung"])
def test_name_length_and_diacritic_boundaries_are_accepted(name):
    assert make(full_name=name).full_name == name


def test_name_in_decomposed_unicode_is_normalised():
    decomposed = "Nguye\u0302\u0303n Va\u0306n An"

    assert make(full_name=decomposed).full_name == "Nguyễn Văn An"


@pytest.mark.parametrize(
    "phone",
    ["", "123456789", "1912345678", "091234567", "09123456789", "09123abcde", " 0912345678"],
)
def test_invalid_phones_are_rejected(phone):
    with pytest.raises(ValidationError):
        make(phone=phone)


def test_birth_date_must_not_be_before_1900():
    with pytest.raises(ValidationError):
        make(birth_date=dt.date(1899, 12, 31))

    assert make(birth_date=dt.date(1900, 1, 1)).birth_date == dt.date(1900, 1, 1)


@pytest.mark.parametrize("gender", ["Khác", "nam", "", "Male"])
def test_gender_must_be_nam_or_nu(gender):
    with pytest.raises(ValidationError):
        make(gender=gender)


def test_female_gender_is_accepted():
    assert make(gender="Nữ").gender == "Nữ"


@pytest.mark.parametrize(
    "email", ["abc", "a@b", "a b@c.vn", "@c.vn", "a@@c.vn", "a" * 250 + "@b.vn"]
)
def test_invalid_emails_are_rejected(email):
    with pytest.raises(ValidationError):
        make(email=email)


def test_email_is_optional_and_blank_becomes_none():
    assert make(email="").email is None
    assert make(email="  ").email is None
    assert make(email="an@example.vn").email == "an@example.vn"


def test_email_of_exactly_254_characters_is_accepted():
    email = "a" * (254 - len("@b.vn")) + "@b.vn"

    assert len(email) == 254
    assert make(email=email).email == email


def test_address_is_optional_trimmed_and_limited_to_255_characters():
    assert make(address=" ").address is None
    assert make(address=" 12 Lê Lợi ").address == "12 Lê Lợi"
    assert len(make(address="a" * 255).address) == 255
    with pytest.raises(ValidationError):
        make(address="a" * 256)


def test_walk_in_request_accepts_profile_id_only():
    assert WalkInRequest(slot_id=1, profile_id=2).new_profile is None


def test_walk_in_request_accepts_new_profile_only():
    assert WalkInRequest(slot_id=1, new_profile=VALID).profile_id is None


def test_walk_in_request_rejects_neither_or_both():
    with pytest.raises(ValidationError):
        WalkInRequest(slot_id=1)
    with pytest.raises(ValidationError):
        WalkInRequest(slot_id=1, profile_id=2, new_profile=VALID)
