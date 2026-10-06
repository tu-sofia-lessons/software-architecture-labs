"""Mini identity provider: issues and verifies signed tokens (provided).

EDUCATIONAL ONLY. In production use an established identity provider (OpenID
Connect / JWT libraries). Never invent your own token format.

Token = base64(payload JSON) + "." + base64(HMAC-SHA256(payload, secret))
"""
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

import users


class InvalidToken(Exception):
    """The token is missing, malformed, tampered with, expired or unknown."""


@dataclass(frozen=True)
class Principal:
    """Who is calling, as proven by a verified token."""
    user: str
    role: str
    student_id: int | None = None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _sign(payload: bytes, secret: str) -> str:
    return _b64(hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest())


def issue_token(user: str, secret: str, ttl_seconds: int = 3600) -> str:
    """Log a user in: return a signed token that expires after ttl_seconds."""
    if user not in users.USERS:
        raise InvalidToken(f"unknown user {user!r}")
    info = users.USERS[user]
    payload = json.dumps({
        "user": user, "role": info["role"], "student_id": info.get("student_id"),
        "exp": int(time.time()) + ttl_seconds,
    }).encode("utf-8")
    return _b64(payload) + "." + _sign(payload, secret)


def verify_token(token: str, secret: str) -> Principal:
    """Return the Principal inside a valid token, or raise InvalidToken."""
    try:
        payload_part, signature = token.split(".")
        payload = base64.urlsafe_b64decode(payload_part)
    except (ValueError, TypeError) as e:
        raise InvalidToken("malformed token") from e
    if not hmac.compare_digest(signature, _sign(payload, secret)):
        raise InvalidToken("bad signature")
    data = json.loads(payload)
    if data["exp"] < time.time():
        raise InvalidToken("token expired")
    if data["user"] not in users.USERS:
        raise InvalidToken("unknown user")
    return Principal(data["user"], data["role"], data.get("student_id"))
