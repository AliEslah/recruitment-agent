from __future__ import annotations

from app.services.otp import generate_otp, hash_otp, verify_otp
from app.services.tokens import generate_token, hash_token, verify_token


def test_token_hash_and_verify() -> None:
    token = generate_token()
    token_hash = hash_token(token)

    assert verify_token(token, token_hash)
    assert not verify_token("wrong", token_hash)


def test_otp_hash_and_verify() -> None:
    otp = generate_otp()
    encoded = hash_otp(otp)

    assert verify_otp(otp, encoded)
    assert not verify_otp("000000", encoded)

