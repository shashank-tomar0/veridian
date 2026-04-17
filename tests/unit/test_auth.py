"""Unit tests for JWT authentication module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestPasswordHashing:
    """Password hash + verify round-trip tests."""

    def test_hash_and_verify_password(self):
        from backend.auth.jwt import hash_password, verify_password

        hashed = hash_password("mysecurepassword")
        assert hashed != "mysecurepassword"
        assert verify_password("mysecurepassword", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_unique(self):
        from backend.auth.jwt import hash_password

        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2  # bcrypt salts should differ


class TestTokenCreation:
    """JWT creation and decoding tests."""

    def test_create_access_token(self):
        from backend.auth.jwt import create_access_token

        token = create_access_token(
            data={"sub": "user@test.com", "permission": "read"}
        )
        assert isinstance(token, str)
        assert len(token) > 10

    def test_decode_access_token(self):
        from backend.auth.jwt import create_access_token, decode_token

        token = create_access_token(
            data={"sub": "user@test.com", "permission": "read"}
        )
        payload = decode_token(token)
        assert payload["sub"] == "user@test.com"
        assert payload["permission"] == "read"

    def test_decode_invalid_token_raises(self):
        from backend.auth.jwt import decode_token

        with pytest.raises(Exception):
            decode_token("invalid.jwt.token")

    def test_create_refresh_token(self):
        from backend.auth.jwt import create_refresh_token

        token = create_refresh_token(data={"sub": "user@test.com"})
        assert isinstance(token, str)

    def test_refresh_token_has_longer_expiry(self):
        from backend.auth.jwt import (
            create_access_token,
            create_refresh_token,
            decode_token,
        )

        access = create_access_token(data={"sub": "u@t.com"})
        refresh = create_refresh_token(data={"sub": "u@t.com"})

        access_payload = decode_token(access)
        refresh_payload = decode_token(refresh)

        assert refresh_payload["exp"] > access_payload["exp"]
