from typing import Optional

from app.common.exception import ConflictError, NotFoundError, ValidationError


class CollocationNotFoundError(NotFoundError):
    """Exception raised when a collocation is not found."""

    def __init__(self, message: str = "Collocation not found.", error_code: Optional[str] = "COLLOCATION_NOT_FOUND"):
        super().__init__(message=message, error_code=error_code)


class CollocationAlreadyExistsError(ConflictError):
    """Exception raised when a collocation already exists."""

    def __init__(self, message: str = "Collocation already exists.", error_code: Optional[str] = "COLLOCATION_ALREADY_EXISTS"):
        super().__init__(message=message, error_code=error_code)


class ExampleSentenceNotFoundError(NotFoundError):
    """Exception raised when an example sentence is not found."""

    def __init__(self, message: str = "Example sentence not found.", error_code: Optional[str] = "EXAMPLE_SENTENCE_NOT_FOUND"):
        super().__init__(message=message, error_code=error_code)


class ExampleSentenceAlreadyExistsError(ConflictError):
    """Exception raised when an example sentence already exists."""

    def __init__(self, message: str = "Example sentence already exists.", error_code: Optional[str] = "EXAMPLE_SENTENCE_ALREADY_EXISTS"):
        super().__init__(message=message, error_code=error_code)


class CollocationDoesNotBelongToItemError(ValidationError):
    """Exception raised when a collocation does not belong to the specified vocabulary item."""

    def __init__(self, message: str = "Collocation does not belong to the specified vocabulary item.", error_code: Optional[str] = "COLLOCATION_DOES_NOT_BELONG_TO_ITEM"):
        super().__init__(message=message, error_code=error_code)
