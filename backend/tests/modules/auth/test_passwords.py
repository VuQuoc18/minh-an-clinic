from app.modules.auth.passwords import hash_password, verify_password


def test_hash_then_verify_succeeds():
    assert verify_password("matkhau123", hash_password("matkhau123"))


def test_wrong_password_fails():
    assert not verify_password("sai-mat-khau", hash_password("matkhau123"))


def test_hash_is_salted_and_does_not_contain_password():
    first, second = hash_password("matkhau123"), hash_password("matkhau123")
    assert first != second
    assert "matkhau123" not in first


def test_unicode_password_roundtrip():
    assert verify_password("mậtKhẩu9", hash_password("mậtKhẩu9"))


def test_malformed_stored_hash_is_not_a_match():
    for stored in ("", "plain", "bcrypt$1$2$3$ab$cd", "scrypt$x$8$1$zz$zz", "scrypt$1$2"):
        assert not verify_password("matkhau123", stored)
