"""Băm và kiểm tra mật khẩu bệnh nhân bằng scrypt của thư viện chuẩn (không thêm dependency).

Dạng lưu: ``scrypt$<n>$<r>$<p>$<salt hex>$<hash hex>``. Dùng chung với màn đặt mật khẩu MH-TK-05
(FR-TK-07) khi màn đó được làm.
"""

import hashlib
import hmac
import secrets

_N = 2**14
_R = 8
_P = 1
_DKLEN = 32
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """So sánh mật khẩu với chuỗi đã băm. Chuỗi lưu sai dạng thì coi là không khớp."""
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)
