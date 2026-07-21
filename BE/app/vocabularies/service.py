import logging
import unicodedata
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.common.time import utc_now
from app.vocabularies.enums import PartOfSpeech
from app.vocabularies.exceptions import (
    VocabularyAlreadyExistsError,
    VocabularyItemAlreadyExistsError,
)
from app.vocabularies.models import Vocabulary, VocabularyItem
from app.vocabularies.schemas import (
    VocabularyCreate,
    VocabularyItemCreate,
    VocabularyItemUpdate,
    VocabularyUpdate,
)

logger = logging.getLogger(__name__)

VOCABULARY_WORD_UNIQUE_INDEX = (
    "uq_vocabularies_deck_id_normalized_word_active"
)
VOCABULARY_ITEM_POSITION_UNIQUE_INDEX = (
    "uq_vocab_items_vocabulary_id_position_active"
)


def _get_constraint_name(error: IntegrityError) -> str | None:
    """Extract a database constraint name from an integrity error."""

    original_error = error.orig
    diagnostic = getattr(original_error, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)

    if constraint_name is None:
        constraint_name = getattr(original_error, "constraint_name", None)

    return constraint_name


def _is_vocabulary_word_conflict(error: IntegrityError) -> bool:
    """Return whether an error came from the active vocabulary-word index."""

    return _get_constraint_name(error) == VOCABULARY_WORD_UNIQUE_INDEX


def _is_vocabulary_item_position_conflict(error: IntegrityError) -> bool:
    """Return whether an error came from the active item-position index."""

    return _get_constraint_name(error) == VOCABULARY_ITEM_POSITION_UNIQUE_INDEX


def _normalize_semantic_text(value: str) -> str:
    """Normalize text for semantic duplicate comparison."""

    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split()).casefold()


def _vocabulary_item_semantic_key(
    part_of_speech: PartOfSpeech,
    english_meaning: str,
    vietnamese_meaning: str,
) -> tuple[PartOfSpeech, str, str]:
    """Build the semantic identity of a vocabulary item."""

    return (
        part_of_speech,
        _normalize_semantic_text(english_meaning),
        _normalize_semantic_text(vietnamese_meaning),
    )


def ensure_no_duplicate_items_in_payload(
    items: Sequence[VocabularyItemCreate],
) -> None:
    """Reject semantically duplicated items in the same request payload."""

    seen_keys: set[tuple[PartOfSpeech, str, str]] = set()

    for item in items:
        semantic_key = _vocabulary_item_semantic_key(
            part_of_speech=item.part_of_speech,
            english_meaning=item.english_meaning,
            vietnamese_meaning=item.vietnamese_meaning,
        )

        if semantic_key in seen_keys:
            raise VocabularyItemAlreadyExistsError(
                "Duplicate vocabulary items were provided."
            )

        seen_keys.add(semantic_key)


def get_semantically_duplicate_vocabulary_item(
    session: Session,
    vocabulary_id: int,
    part_of_speech: PartOfSpeech,
    english_meaning: str,
    vietnamese_meaning: str,
    exclude_item_id: int | None = None,
) -> VocabularyItem | None:
    """Find an active item with the same part of speech and meanings."""

    statement = select(VocabularyItem).where(
        VocabularyItem.vocabulary_id == vocabulary_id,
        VocabularyItem.part_of_speech == part_of_speech,
        VocabularyItem.is_deleted.is_(False),
    )

    if exclude_item_id is not None:
        statement = statement.where(VocabularyItem.id != exclude_item_id)

    target_key = _vocabulary_item_semantic_key(
        part_of_speech=part_of_speech,
        english_meaning=english_meaning,
        vietnamese_meaning=vietnamese_meaning,
    )

    for item in session.exec(statement).all():
        item_key = _vocabulary_item_semantic_key(
            part_of_speech=item.part_of_speech,
            english_meaning=item.english_meaning,
            vietnamese_meaning=item.vietnamese_meaning,
        )
        if item_key == target_key:
            return item

    return None


def ensure_vocabulary_item_is_not_duplicate(
    session: Session,
    vocabulary_id: int,
    part_of_speech: PartOfSpeech,
    english_meaning: str,
    vietnamese_meaning: str,
    exclude_item_id: int | None = None,
) -> None:
    """Raise a conflict when an equivalent active item already exists."""

    duplicate_item = get_semantically_duplicate_vocabulary_item(
        session=session,
        vocabulary_id=vocabulary_id,
        part_of_speech=part_of_speech,
        english_meaning=english_meaning,
        vietnamese_meaning=vietnamese_meaning,
        exclude_item_id=exclude_item_id,
    )

    if duplicate_item is not None:
        raise VocabularyItemAlreadyExistsError(
            "A vocabulary item with the same part of speech and meanings "
            "already exists."
        )


def get_vocabulary_by_id_including_deleted(
    session: Session,
    vocabulary_id: int,
) -> Vocabulary | None:
    """Retrieve a vocabulary by ID, including soft-deleted records."""

    return session.get(Vocabulary, vocabulary_id)


def get_active_vocabulary_by_id(
    session: Session,
    vocabulary_id: int,
) -> Vocabulary | None:
    """Retrieve an active vocabulary by ID."""

    statement = select(Vocabulary).where(
        Vocabulary.id == vocabulary_id,
        Vocabulary.is_deleted.is_(False),
    )

    return session.exec(statement).first()


def get_active_vocabulary_by_normalized_word(
    session: Session,
    deck_id: int,
    normalized_word: str,
) -> Vocabulary | None:
    """Retrieve an active vocabulary by normalized word within a deck."""

    statement = select(Vocabulary).where(
        Vocabulary.deck_id == deck_id,
        Vocabulary.normalized_word == normalized_word,
        Vocabulary.is_deleted.is_(False),
    )

    return session.exec(statement).first()


def get_active_vocabularies_in_deck(
    session: Session,
    deck_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[Vocabulary]:
    """Retrieve active vocabularies in a deck with pagination."""

    statement = (
        select(Vocabulary)
        .where(
            Vocabulary.deck_id == deck_id,
            Vocabulary.is_deleted.is_(False),
        )
        .order_by(
            Vocabulary.created_at.desc(),
            Vocabulary.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def get_vocabularies_for_admin(
    session: Session,
    include_deleted: bool = False,
    deck_id: int | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Vocabulary]:
    """Retrieve vocabularies for administrators with optional filters."""

    statement = select(Vocabulary)

    if not include_deleted:
        statement = statement.where(col(Vocabulary.is_deleted).is_(False))

    if deck_id is not None:
        statement = statement.where(Vocabulary.deck_id == deck_id)

    if query is not None:
        normalized_query = _normalize_semantic_text(query)
        if normalized_query:
            statement = statement.where(
                col(Vocabulary.normalized_word).contains(
                    normalized_query,
                    autoescape=True,
                )
            )

    statement = (
        statement
        .order_by(Vocabulary.created_at.desc(), Vocabulary.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def get_active_vocabulary_item_by_id(
    session: Session,
    vocabulary_item_id: int,
) -> VocabularyItem | None:
    """Retrieve an active vocabulary item by ID."""

    statement = select(VocabularyItem).where(
        VocabularyItem.id == vocabulary_item_id,
        VocabularyItem.is_deleted.is_(False),
    )

    return session.exec(statement).first()


def get_all_active_items_in_vocabulary(
    session: Session,
    vocabulary_id: int,
) -> list[VocabularyItem]:
    """Retrieve all active items in display order for a vocabulary."""

    statement = select(VocabularyItem).where(
        VocabularyItem.vocabulary_id == vocabulary_id,
        VocabularyItem.is_deleted.is_(False),
    ).order_by(
        VocabularyItem.position.asc(),
        VocabularyItem.id.asc(),
    )

    return session.exec(statement).all()


def get_all_items_in_vocabulary_including_deleted(
    session: Session,
    vocabulary_id: int,
) -> list[VocabularyItem]:
    """Retrieve all items for an administrator, including deleted items."""

    statement = (
        select(VocabularyItem)
        .where(VocabularyItem.vocabulary_id == vocabulary_id)
        .order_by(
            VocabularyItem.position.asc(),
            VocabularyItem.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_next_vocabulary_item_position(
    session: Session,
    vocabulary_id: int,
) -> int:
    """Return one position after the highest active item position."""

    statement = (
        select(VocabularyItem.position)
        .where(
            VocabularyItem.vocabulary_id == vocabulary_id,
            VocabularyItem.is_deleted.is_(False),
        )
        .order_by(VocabularyItem.position.desc())
        .limit(1)
    )
    highest_position = session.exec(statement).first()

    return (highest_position or 0) + 1


def create_vocabulary(
    session: Session,
    deck_id: int,
    vocabulary_create: VocabularyCreate,
) -> Vocabulary:
    """Create a vocabulary and its items in one transaction."""

    normalized_word = _normalize_semantic_text(vocabulary_create.word)
    existing_vocabulary = get_active_vocabulary_by_normalized_word(
        session=session,
        deck_id=deck_id,
        normalized_word=normalized_word,
    )

    if existing_vocabulary is not None:
        raise VocabularyAlreadyExistsError(
            f"Vocabulary '{vocabulary_create.word}' already exists in this deck."
        )

    ensure_no_duplicate_items_in_payload(vocabulary_create.items)

    new_vocabulary = Vocabulary(
        deck_id=deck_id,
        word=vocabulary_create.word,
        normalized_word=normalized_word,
    )

    try:
        session.add(new_vocabulary)
        session.flush()

        if new_vocabulary.id is None:
            raise RuntimeError("Vocabulary ID was not generated after flush.")

        new_items = [
            VocabularyItem(
                vocabulary_id=new_vocabulary.id,
                position=position,
                **item_create.model_dump(),
            )
            for position, item_create in enumerate(
                vocabulary_create.items,
                start=1,
            )
        ]

        session.add_all(new_items)
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_vocabulary_word_conflict(error):
            raise VocabularyAlreadyExistsError(
                f"Vocabulary '{vocabulary_create.word}' already exists in this deck."
            ) from error

        logger.exception(
            "Failed to create vocabulary '%s' in deck %s.",
            vocabulary_create.word,
            deck_id,
        )
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to create vocabulary '%s' in deck %s.",
            vocabulary_create.word,
            deck_id,
        )
        raise

    session.refresh(new_vocabulary)
    return new_vocabulary


def update_vocabulary(
    session: Session,
    vocabulary: Vocabulary,
    vocabulary_update: VocabularyUpdate,
) -> Vocabulary:
    """Update a persisted, active vocabulary."""

    if vocabulary_update.word is not None:
        normalized_word = _normalize_semantic_text(vocabulary_update.word)
        existing_vocabulary = get_active_vocabulary_by_normalized_word(
            session=session,
            deck_id=vocabulary.deck_id,
            normalized_word=normalized_word,
        )

        if (
            existing_vocabulary is not None
            and existing_vocabulary.id != vocabulary.id
        ):
            raise VocabularyAlreadyExistsError(
                f"Vocabulary '{vocabulary_update.word}' already exists in this deck."
            )

        vocabulary.word = vocabulary_update.word
        vocabulary.normalized_word = normalized_word

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_vocabulary_word_conflict(error):
            raise VocabularyAlreadyExistsError(
                f"Vocabulary '{vocabulary_update.word}' already exists in this deck."
            ) from error

        logger.exception("Failed to update vocabulary %s.", vocabulary.id)
        raise
    except Exception:
        session.rollback()
        logger.exception("Failed to update vocabulary %s.", vocabulary.id)
        raise

    session.refresh(vocabulary)
    return vocabulary


def delete_vocabulary(session: Session, vocabulary: Vocabulary) -> None:
    """Soft-delete a vocabulary and all its active items."""

    if vocabulary.id is None:
        raise RuntimeError("Cannot delete a vocabulary without an ID.")

    deleted_at = utc_now()
    vocabulary.is_deleted = True
    vocabulary.deleted_at = deleted_at

    items = get_all_active_items_in_vocabulary(
        session=session,
        vocabulary_id=vocabulary.id,
    )
    for item in items:
        item.is_deleted = True
        item.deleted_at = deleted_at

    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to delete vocabulary %s.", vocabulary.id)
        raise


def create_vocabulary_item(
    session: Session,
    vocabulary: Vocabulary,
    item_create: VocabularyItemCreate,
) -> VocabularyItem:
    """Create an item in a persisted, active vocabulary."""

    if vocabulary.id is None:
        raise RuntimeError("Cannot create an item for a vocabulary without an ID.")

    ensure_vocabulary_item_is_not_duplicate(
        session=session,
        vocabulary_id=vocabulary.id,
        part_of_speech=item_create.part_of_speech,
        english_meaning=item_create.english_meaning,
        vietnamese_meaning=item_create.vietnamese_meaning,
    )

    new_item = VocabularyItem(
        vocabulary_id=vocabulary.id,
        position=get_next_vocabulary_item_position(
            session=session,
            vocabulary_id=vocabulary.id,
        ),
        **item_create.model_dump(),
    )

    try:
        session.add(new_item)
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_vocabulary_item_position_conflict(error):
            raise VocabularyItemAlreadyExistsError(
                "A concurrent request created an item at the same position."
            ) from error

        logger.exception(
            "Failed to create an item for vocabulary %s.",
            vocabulary.id,
        )
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to create an item for vocabulary %s.",
            vocabulary.id,
        )
        raise

    session.refresh(new_item)
    return new_item


def update_vocabulary_item(
    session: Session,
    item: VocabularyItem,
    item_update: VocabularyItemUpdate,
) -> VocabularyItem:
    """Partially update a persisted, active vocabulary item."""

    if item.id is None:
        raise RuntimeError("Cannot update a vocabulary item without an ID.")

    part_of_speech = item.part_of_speech
    english_meaning = item.english_meaning
    vietnamese_meaning = item.vietnamese_meaning

    if "part_of_speech" in item_update.model_fields_set:
        if item_update.part_of_speech is None:
            raise RuntimeError("Validated part of speech cannot be None.")
        part_of_speech = item_update.part_of_speech

    if "english_meaning" in item_update.model_fields_set:
        if item_update.english_meaning is None:
            raise RuntimeError("Validated English meaning cannot be None.")
        english_meaning = item_update.english_meaning

    if "vietnamese_meaning" in item_update.model_fields_set:
        if item_update.vietnamese_meaning is None:
            raise RuntimeError("Validated Vietnamese meaning cannot be None.")
        vietnamese_meaning = item_update.vietnamese_meaning

    ensure_vocabulary_item_is_not_duplicate(
        session=session,
        vocabulary_id=item.vocabulary_id,
        part_of_speech=part_of_speech,
        english_meaning=english_meaning,
        vietnamese_meaning=vietnamese_meaning,
        exclude_item_id=item.id,
    )

    update_data = item_update.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_data)

    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to update vocabulary item %s.", item.id)
        raise

    session.refresh(item)
    return item


def delete_vocabulary_item(session: Session, item: VocabularyItem) -> None:
    """Soft-delete a persisted, active vocabulary item."""

    if item.id is None:
        raise RuntimeError("Cannot delete a vocabulary item without an ID.")

    item.is_deleted = True
    item.deleted_at = utc_now()

    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to delete vocabulary item %s.", item.id)
        raise
