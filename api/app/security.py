from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt

from app.config import get_settings

TokenKind = Literal["access", "refresh"]


class InvalidToken(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: int, kind: TokenKind) -> str:
    settings = get_settings()
    lifetime = (
        timedelta(minutes=settings.access_token_minutes)
        if kind == "access"
        else timedelta(days=settings.refresh_token_days)
    )
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": kind, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_kind: TokenKind) -> int:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidToken from exc
    # Un jeton de rafraîchissement ne doit pas pouvoir servir de jeton d'accès.
    if payload.get("type") != expected_kind:
        raise InvalidToken
    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidToken from exc
