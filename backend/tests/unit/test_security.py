from __future__ import annotations

import time

import pytest
from jose import JWTError

from app.services.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_round_trip():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_is_not_plaintext():
    assert hash_password("secret123") != "secret123"


def test_access_token_round_trip():
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_access_token_wrong_type_rejected():
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.core.config import settings

    payload = {"sub": "u1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "type": "refresh"}
    bad_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    with pytest.raises(JWTError):
        decode_access_token(bad_token)


def test_refresh_token_uniqueness():
    tokens = {generate_refresh_token() for _ in range(100)}
    assert len(tokens) == 100


def test_refresh_token_hash_deterministic():
    raw = generate_refresh_token()
    assert hash_refresh_token(raw) == hash_refresh_token(raw)


def test_different_tokens_different_hashes():
    a, b = generate_refresh_token(), generate_refresh_token()
    assert hash_refresh_token(a) != hash_refresh_token(b)
