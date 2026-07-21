from typing import Optional

from app.common.exception import ConflictError, NotFoundError

class VocabularyNotFoundError(NotFoundError):
    """Exception raised when a vocabulary is not found."""

    def __init__(self, message: str = "Vocabulary not found.", error_code: Optional[str] = "VOCABULARY_NOT_FOUND"):
        super().__init__(message=message, error_code=error_code)


class VocabularyAlreadyExistsError(ConflictError):
    """Exception raised when a vocabulary already exists."""

    def __init__(self, message: str = "Vocabulary already exists.", error_code: Optional[str] = "VOCABULARY_ALREADY_EXISTS"):
        super().__init__(message=message, error_code=error_code)


class VocabularyItemNotFoundError(NotFoundError):
    """Exception raised when a vocabulary item is not found."""

    def __init__(self, message: str = "Vocabulary item not found.", error_code: Optional[str] = "VOCABULARY_ITEM_NOT_FOUND"):
        super().__init__(message=message, error_code=error_code)


class VocabularyItemAlreadyExistsError(ConflictError):
    """Exception raised when a vocabulary item already exists."""

    def __init__(self, message: str = "Vocabulary item already exists.", error_code: Optional[str] = "VOCABULARY_ITEM_ALREADY_EXISTS"):
        super().__init__(message=message, error_code=error_code)
