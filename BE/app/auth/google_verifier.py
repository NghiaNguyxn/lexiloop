import secrets
from typing import Any, Mapping

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import ValidationError as PydanticValidationError

from app.auth.exceptions import (
    InvalidGoogleNonceError,
    InvalidGoogleTokenError,
    UnverifiedGoogleEmailError,
)
from app.auth.schemas import GoogleIdentityData
from app.common.exception import InternalServerError
from app.core.config import settings


_GOOGLE_ISSUERS = {
    "accounts.google.com",
    "https://accounts.google.com",
}


def verify_google_credential(
    credential: str,
    expected_nonce: str,
) -> GoogleIdentityData:
    """Verify a Google credential and return the identity data."""

    if not isinstance(expected_nonce, str) or not expected_nonce:
        raise InvalidGoogleNonceError()

    try:
        claims: Mapping[str, Any] = (
            google_id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                audience=settings.GOOGLE_CLIENT_ID,
            )
        )
    except TransportError as e:
        raise InternalServerError(message="Google sign-in is temporarily unavailable.",) from e
    except (GoogleAuthError, ValueError) as e:
        # Signature, audience, issuer, expiry or token format is invalid.
        raise InvalidGoogleTokenError() from e

    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise InvalidGoogleTokenError()

    if claims.get("iss") not in _GOOGLE_ISSUERS:
        raise InvalidGoogleTokenError()

    token_nonce = claims.get("nonce")

    if (
        not isinstance(token_nonce, str)
        or not secrets.compare_digest(
            token_nonce.encode("utf-8"),
            expected_nonce.encode("utf-8")
        )
    ):
        raise InvalidGoogleNonceError()

    if claims.get("email_verified") is not True:
        raise UnverifiedGoogleEmailError()

    subject = claims.get("sub")
    email = claims.get("email")

    if not isinstance(subject, str) or not subject.strip():
        raise InvalidGoogleTokenError()

    if not isinstance(email, str) or not email.strip():
        raise InvalidGoogleTokenError()

    full_name = _get_optional_string(claims.get("name"))
    avatar_url = _get_optional_string(claims.get("picture"))

    try:
        return GoogleIdentityData(
            subject=subject.strip(),
            email=email.strip().lower(),
            full_name=full_name,
            avatar_url=avatar_url,
        )
    except PydanticValidationError as e:
        raise InvalidGoogleTokenError() from e


def _get_optional_string(value: object) -> str | None:
    """Return the string value if it's a non-empty string, otherwise return None."""

    if not isinstance(value, str):
        return None

    return value.strip() or None
