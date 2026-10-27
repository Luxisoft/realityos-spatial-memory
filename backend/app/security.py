from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import Settings


def hash_password(password: str) -> str:
    """Hash using scrypt with a unique salt; no reversible password data is stored."""
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    n, r, p = 2**14, 8, 1
    derived = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p)
    return "$".join(
        (
            "scrypt",
            str(n),
            str(r),
            str(p),
            base64.urlsafe_b64encode(salt).decode(),
            base64.urlsafe_b64encode(derived).decode(),
        )
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, encoded_salt, expected = encoded.split("$")
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=base64.urlsafe_b64decode(encoded_salt.encode()),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected.encode()))
    except (ValueError, TypeError):
        return False


def create_device_credential() -> str:
    """Generate a high-entropy credential displayed exactly once to an administrator."""

    return secrets.token_urlsafe(32)


def hash_device_credential(credential: str, settings: Settings) -> str:
    """Store a peppered digest, not a reusable device credential."""

    return hmac.new(
        (settings.device_credential_pepper or settings.jwt_secret).encode(),
        credential.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_device_credential(credential: str, expected_hash: str, settings: Settings) -> bool:
    return hmac.compare_digest(hash_device_credential(credential, settings), expected_hash)


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID, settings: Settings) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=settings.refresh_token_days)
    jti = secrets.token_urlsafe(32)
    payload = {"sub": str(user_id), "typ": "refresh", "jti": jti, "iat": now, "exp": expires_at}
    return (
        jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm),
        jti,
        expires_at,
    )


def decode_token(token: str, settings: Settings, expected_type: str) -> dict[str, object]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("typ") != expected_type or not payload.get("sub"):
        raise jwt.InvalidTokenError("Unexpected token type.")
    return payload


def create_display_evidence_token(
    observation_id: uuid.UUID, device_id: uuid.UUID, settings: Settings
) -> str:
    """Create a short-lived, observation-specific URL credential for Display.

    The DAT Display image component loads an HTTPS URL itself and therefore
    cannot include RealityOS device headers. This token never grants API access
    beyond rendering the single highlighted observation it names.
    """

    now = datetime.now(UTC)
    payload = {
        "sub": str(observation_id),
        "did": str(device_id),
        "typ": "display_evidence",
        "iat": now,
        "exp": now + timedelta(minutes=settings.display_evidence_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_display_evidence_token(token: str, settings: Settings) -> tuple[uuid.UUID, uuid.UUID]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("typ") != "display_evidence":
        raise jwt.InvalidTokenError("Unexpected token type.")
    try:
        return uuid.UUID(str(payload["sub"])), uuid.UUID(str(payload["did"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Invalid display evidence token.") from exc
