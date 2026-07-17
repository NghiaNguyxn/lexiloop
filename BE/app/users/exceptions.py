from typing import Optional

from app.common.exception import ConflictError, ForbiddenError, NotFoundError

class UserNotFoundError(NotFoundError):
    """Exception raised when a user is not found."""

    def __init__(self, message: str = "User not found.", error_code: Optional[str] = "USER_NOT_FOUND"):
        super().__init__(message=message, error_code=error_code)

class UserInactiveError(ForbiddenError):
    """Exception raised when a user is inactive."""

    def __init__(self, message: str = "User is inactive.", error_code: Optional[str] = "USER_INACTIVE"):
        super().__init__(message=message, error_code=error_code)

class UserAlreadyExistsError(ConflictError):
    """Exception raised when a user already exists."""

    def __init__(self, message: str = "User already exists.", error_code: Optional[str] = "USER_ALREADY_EXISTS"):
        super().__init__(message=message, error_code=error_code)
