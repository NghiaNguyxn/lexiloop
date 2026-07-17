import logging
import unicodedata

from sqlmodel import Session, col, select
from sqlalchemy.exc import IntegrityError

from app.users.models import User
from app.decks.models import Deck
from app.decks.schemas import DeckCreate, DeckUpdate
from app.decks.exceptions import DeckAlreadyExistsError
from app.common.time import utc_now

logger = logging.getLogger(__name__)

DECK_NAME_UNIQUE_INDEX = "uq_decks_user_id_normalized_name_active"


def _is_deck_name_conflict(error: IntegrityError) -> bool:
    """Return whether an integrity error came from the active deck-name index."""

    original_error = error.orig
    diagnostic = getattr(original_error, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)

    if constraint_name is None:
        constraint_name = getattr(original_error, "constraint_name", None)

    return constraint_name == DECK_NAME_UNIQUE_INDEX


def get_active_owned_deck_by_id(session: Session, deck_id: int, user_id: int) -> Deck | None:
    """Retrieve an active (not deleted) deck by its ID and user ID."""

    statement = select(Deck).where(
        Deck.id == deck_id,
        Deck.user_id == user_id,
        Deck.is_deleted.is_(False),
    )

    return session.exec(statement).first()


def get_deck_by_id_including_deleted(
    session: Session,
    deck_id: int,
) -> Deck | None:
    """Retrieve a deck by ID for administrative use, including deleted decks."""

    return session.get(Deck, deck_id)


def get_readable_deck_by_id(session: Session, deck_id: int, user_id: int) -> Deck | None:
    """Retrieve a deck by its ID that is either owned by the user or is public and not deleted."""

    statement = select(Deck).join(User).where(
        Deck.id == deck_id,
        (Deck.user_id == user_id) | Deck.is_public.is_(True),
        Deck.is_deleted.is_(False),
        User.is_deleted.is_(False),
    )

    return session.exec(statement).first()


def get_active_owned_deck_by_normalized_name(session: Session, normalized_name: str, user_id: int) -> Deck | None:
    """Retrieve an active (not deleted) deck by its normalized name and user ID."""

    statement = select(Deck).where(
        Deck.normalized_name == normalized_name,
        Deck.user_id == user_id,
        Deck.is_deleted.is_(False),
    )

    return session.exec(statement).first()


def get_user_decks(session: Session, user_id: int, limit: int = 50, offset: int = 0) -> list[Deck]:
    """Retrieve active decks owned by a specific user."""

    statement = (
        select(Deck)
        .where(
            Deck.user_id == user_id,
            Deck.is_deleted.is_(False),
        )
        .order_by(Deck.created_at.desc(), Deck.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def get_public_decks(session: Session, limit: int = 50, offset: int = 0) -> list[Deck]:
    """Retrieve all public decks that are not deleted."""

    statement = (
        select(Deck)
        .join(User)
        .where(
            Deck.is_public.is_(True),
            Deck.is_deleted.is_(False),
            User.is_deleted.is_(False),
        )
        .order_by(Deck.created_at.desc(), Deck.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def get_decks_for_admin(
    session: Session,
    include_deleted: bool = False,
    user_id: int | None = None,
    is_public: bool | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Deck]:
    """Retrieve decks for administrators with optional filters."""

    statement = select(Deck)

    if not include_deleted:
        statement = statement.where(col(Deck.is_deleted).is_(False))

    if user_id is not None:
        statement = statement.where(Deck.user_id == user_id)

    if is_public is not None:
        statement = statement.where(col(Deck.is_public).is_(is_public))

    if query is not None:
        normalized_query = unicodedata.normalize("NFKC", query)
        normalized_query = " ".join(normalized_query.split()).casefold()
        if normalized_query:
            statement = statement.where(
                col(Deck.normalized_name).contains(
                    normalized_query,
                    autoescape=True,
                )
            )

    statement = (
        statement
        .order_by(Deck.created_at.desc(), Deck.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def create_deck(session: Session, deck_create: DeckCreate, user_id: int) -> Deck:
    """Create a new deck for a specific user."""

    if get_active_owned_deck_by_normalized_name(session, deck_create.name.casefold(), user_id):
        logger.error(f"Deck creation failed: A deck with the name '{deck_create.name}' already exists for user {user_id}.")
        raise DeckAlreadyExistsError(f"A deck with the name '{deck_create.name}' already exists for this user.")

    new_deck = Deck(
        user_id=user_id,
        name=deck_create.name,
        normalized_name=deck_create.name.casefold(),
        description=deck_create.description,
        is_public=deck_create.is_public,
    )

    session.add(new_deck)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _is_deck_name_conflict(error):
            logger.warning(
                "Deck creation failed because name '%s' already exists for user %s.",
                deck_create.name,
                user_id,
            )
            raise DeckAlreadyExistsError(
                f"A deck with the name '{deck_create.name}' already exists for this user."
            ) from error

        logger.exception("Failed to create deck for user %s.", user_id)
        raise
    session.refresh(new_deck)

    return new_deck


def update_deck(session: Session, deck: Deck, deck_update: DeckUpdate) -> Deck:
    """Update an existing deck owned by a specific user."""

    if deck_update.name is not None:
        deck.name = deck_update.name
        deck.normalized_name = deck_update.name.casefold()
    if "description" in deck_update.model_fields_set:
        deck.description = deck_update.description
    if deck_update.is_public is not None:
        deck.is_public = deck_update.is_public


    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _is_deck_name_conflict(error):
            logger.warning(
                "Deck update failed because name '%s' already exists for user %s.",
                deck_update.name,
                deck.user_id,
            )
            raise DeckAlreadyExistsError(
                f"A deck with the name '{deck_update.name}' already exists for this user."
            ) from error

        logger.exception(
            "Failed to update deck with ID %s for user %s.",
            deck.id,
            deck.user_id,
        )
        raise

    session.refresh(deck)
    return deck


def delete_deck(session: Session, deck: Deck) -> None:
    """Soft delete a deck owned by a specific user."""

    deck.is_public = False
    deck.is_deleted = True
    deck.deleted_at = utc_now()

    session.add(deck)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete deck with ID {deck.id} for user {deck.user_id}: {e}")
        raise
