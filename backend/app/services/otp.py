from __future__ import annotations

import hashlib
import secrets


def generate_otp(length: int = 6) -> str:
    upper = 10**length
    value = secrets.randbelow(upper)
    return f"{value:0{length}d}"


def hash_otp(otp: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", otp.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def verify_otp(otp: str, encoded: str | None) -> bool:
    if not encoded or "$" not in encoded:
        return False
    salt, digest_hex = encoded.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", otp.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return secrets.compare_digest(candidate, digest_hex)

