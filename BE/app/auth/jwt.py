import jwt
import secrets
from datetime import datetime, timedelta
from pydantic import ValidationError as PydanticValidationError

from app.auth.exceptions import ExpiredAccessTokenError, InvalidAccessTokenError
from app.auth.schemas import AccessTokenData
from app.common.time import add_days, add_minutes, utc_now
from app.core.config import settings

def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""

    to_encode = {"user_id": user_id, "token_type": "access"}
    if expires_delta:
        expire = add_minutes(utc_now(), expires_delta.total_seconds() / 60)
    else:
        expire = add_minutes(utc_now(), settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

def verify_access_token(token: str) -> AccessTokenData:
    """Verify a JWT access token and return the decoded data."""

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("token_type")

        if user_id is None or token_type != "access":
            raise InvalidAccessTokenError()

        return AccessTokenData(user_id=user_id, token_type=token_type)

    except jwt.ExpiredSignatureError as exc:
        raise ExpiredAccessTokenError() from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidAccessTokenError() from exc
    except (PydanticValidationError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError() from exc

def create_refresh_token() -> str:
    """Create a refresh token."""

    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    """Hash a refresh token using SHA256."""

    import hashlib
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def get_refresh_token_expiration() -> datetime:
    """Calculate the expiration datetime for a refresh token."""

    return add_days(utc_now(), settings.REFRESH_TOKEN_EXPIRE_DAYS)

def get_refresh_cookie_max_age() -> int:
    """Get the max age for the refresh token cookie in seconds."""

    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

def verify_refresh_token(token: str, hashed_token: str) -> bool:
    """Verify a refresh token against its hashed version."""

    return hash_refresh_token(token) == hashed_token
