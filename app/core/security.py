from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str | int, expires_delta: timedelta, token_type: str) -> str:
    expire_at = datetime.now(UTC) + expires_delta
    claims: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire_at,
        "type": token_type,
    }
    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str | int) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expires_minutes)
    return create_token(subject, expires_delta, token_type="access")


def create_refresh_token(subject: str | int) -> str:
    expires_delta = timedelta(minutes=settings.refresh_token_expires_minutes)
    return create_token(subject, expires_delta, token_type="refresh")


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as exc:  # pragma: no cover - external library detail
        raise ValueError("Invalid token") from exc
