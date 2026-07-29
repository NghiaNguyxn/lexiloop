from typing import Optional

from app.common.exception import (
    ConflictError,
    ForbiddenError,
    UnAuthorizedError,
    ValidationError,
)

class InvalidCredentialsError(UnAuthorizedError):
    """Exception raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials.", error_code: Optional[str] = "INVALID_CREDENTIALS"):
        super().__init__(message=message, error_code=error_code)

class InvalidCurrentPasswordError(UnAuthorizedError):
    """Exception raised when the current password is invalid."""

    def __init__(self, message: str = "Invalid current password.", error_code: Optional[str] = "INVALID_CURRENT_PASSWORD"):
        super().__init__(message=message, error_code=error_code)

class PasswordSameAsOldError(ValidationError):
    """Exception raised when the new password is the same as the old password."""

    def __init__(self, message: str = "New password cannot be the same as the old password.", error_code: Optional[str] = "PASSWORD_SAME_AS_OLD"):
        super().__init__(message=message, error_code=error_code)

class ExpiredAccessTokenError(UnAuthorizedError):
    """Exception raised when an access token has expired."""

    def __init__(self, message: str = "Access token has expired.", error_code: Optional[str] = "ACCESS_TOKEN_EXPIRED"):
        super().__init__(message=message, error_code=error_code)

class InvalidAccessTokenError(UnAuthorizedError):
    """Exception raised when an access token is invalid."""

    def __init__(self, message: str = "Access token is invalid.", error_code: Optional[str] = "ACCESS_TOKEN_INVALID"):
        super().__init__(message=message, error_code=error_code)

class MissingRefreshTokenError(UnAuthorizedError):
    """Exception raised when a refresh token is missing."""

    def __init__(self, message: str = "Refresh token is missing.", error_code: Optional[str] = "REFRESH_TOKEN_MISSING"):
        super().__init__(message=message, error_code=error_code)

class InvalidRefreshTokenError(UnAuthorizedError):
    """Exception raised when a refresh token is invalid."""

    def __init__(self, message: str = "Refresh token is invalid.", error_code: Optional[str] = "REFRESH_TOKEN_INVALID"):
        super().__init__(message=message, error_code=error_code)

class ExpiredRefreshTokenError(UnAuthorizedError):
    """Exception raised when a refresh token has expired."""

    def __init__(self, message: str = "Refresh token has expired.", error_code: Optional[str] = "REFRESH_TOKEN_EXPIRED"):
        super().__init__(message=message, error_code=error_code)


class RefreshTokenReuseError(UnAuthorizedError):
    """Exception raised when a refresh token is reused."""

    def __init__(self, message: str = "Refresh token has been reused.", error_code: Optional[str] = "REFRESH_TOKEN_REUSED"):
        super().__init__(message=message, error_code=error_code)


class InvalidGoogleTokenError(UnAuthorizedError):
    """Exception raised when a Google token is invalid."""

    def __init__(self, message: str = "Google credential is invalid.", error_code: Optional[str] = "INVALID_GOOGLE_TOKEN"):
        super().__init__(message=message, error_code=error_code)


class UnverifiedGoogleEmailError(UnAuthorizedError):
    """Exception raised when a Google email is unverified."""

    def __init__(self, message: str = "Google email is not verified.", error_code: Optional[str] = "UNVERIFIED_GOOGLE_EMAIL"):
        super().__init__(message=message, error_code=error_code)


class InvalidGoogleNonceError(UnAuthorizedError):
    """Exception raised when a Google nonce is invalid."""

    def __init__(self, message: str = "Google sign-in request is invalid or expired.", error_code: Optional[str] = "INVALID_GOOGLE_NONCE"):
        super().__init__(message=message, error_code=error_code)


class GoogleLinkRequiredError(ConflictError):
    """Exception raised when a Google account needs to be linked."""

    def __init__(
        self,
        message: str = (
            "An account with this email already exists. "
            "Sign in and link Google from your account settings."
        ),
        error_code: Optional[str] = "GOOGLE_LINK_REQUIRED"
    ):
        super().__init__(message=message, error_code=error_code)


class GoogleIdentityAlreadyLinkedError(ConflictError):
    """Exception raised when a Google identity is already linked to another user."""

    def __init__(self, message: str = "This Google account is linked to another user.", error_code: Optional[str] = "GOOGLE_IDENTITY_ALREADY_LINKED"):
        super().__init__(message=message, error_code=error_code)


class GoogleAlreadyLinkedError(ConflictError):
    """Exception raised when a Google account is already linked to the current user."""

    def __init__(self, message: str = "A Google account is already linked to this user.", error_code: Optional[str] = "GOOGLE_ALREADY_LINKED"):
        super().__init__(message=message, error_code=error_code)


class GoogleUnlinkNotAllowedError(ConflictError):
    """Exception raised when unlinking a Google account is not allowed."""

    def __init__(self, message: str = "Google cannot be unlinked because it is your only sign-in method.", error_code: Optional[str] = "GOOGLE_UNLINK_NOT_ALLOWED"):
        super().__init__(message=message, error_code=error_code)


class AccountUnavailableError(ForbiddenError):
    """Exception raised when an account is unavailable."""

    def __init__(self, message: str = "This account is unavailable.", error_code: Optional[str] = "ACCOUNT_UNAVAILABLE"):
        super().__init__(message=message, error_code=error_code)


class PasswordNotConfiguredError(ConflictError):
    """Exception raised when a password is not configured for the account."""

    def __init__(self, message: str = "A password is not configured for this account.", error_code: Optional[str] = "PASSWORD_NOT_CONFIGURED"):
        super().__init__(message=message, error_code=error_code)
