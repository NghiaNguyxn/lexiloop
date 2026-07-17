from typing import Optional

from ..common.exception import AppError, ValidationError, UnAuthorizedError, ForbiddenError, NotFoundError, ConflictError, InternalServerError

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
