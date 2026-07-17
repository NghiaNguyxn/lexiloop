from typing import Optional
from app.common.exception import NotFoundError, ConflictError

class DeckNotFoundError(NotFoundError):
    """Exception raised when a requested deck is not found."""

    def __init__(self, message: str = "Deck not found.", error_code: Optional[str] = "DECK_NOT_FOUND"):
        super().__init__(message=message, error_code=error_code)


class DeckAlreadyExistsError(ConflictError):
    """Exception raised when a deck already exists."""

    def __init__(self, message: str = "Deck already exists.", error_code: Optional[str] = "DECK_ALREADY_EXISTS"):
        super().__init__(message=message, error_code=error_code)
