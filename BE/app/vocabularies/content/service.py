import logging
import unicodedata
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.common.time import utc_now
from app.vocabularies.content.exceptions import (
    CollocationAlreadyExistsError,
    CollocationDoesNotBelongToItemError,
    CollocationNotFoundError,
    ExampleSentenceAlreadyExistsError,
)
from app.vocabularies.content.models import Collocation, ExampleSentence
from app.vocabularies.content.schemas import (
    CollocationCreate,
    CollocationUpdate,
    ExampleSentenceCreate,
    ExampleSentenceUpdate,
)

logger = logging.getLogger(__name__)

COLLOCATION_PHRASE_UNIQUE_INDEX = (
    "uq_collocations_vocabulary_item_id_normalized_phrase_active"
)
EXAMPLE_SENTENCE_UNIQUE_INDEX = (
    "uq_examples_item_normalized_sentence_active"
)


def _get_constraint_name(error: IntegrityError) -> str | None:
    """Extract a database constraint name from an integrity error."""

    original_error = error.orig
    diagnostic = getattr(original_error, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)

    if constraint_name is None:
        constraint_name = getattr(original_error, "constraint_name", None)

    return constraint_name


def _is_collocation_phrase_conflict(error: IntegrityError) -> bool:
    """Return whether an error came from the active-phrase index."""

    return _get_constraint_name(error) == COLLOCATION_PHRASE_UNIQUE_INDEX


def _is_example_sentence_conflict(error: IntegrityError) -> bool:
    """Return whether an error came from the active-sentence index."""

    return _get_constraint_name(error) == EXAMPLE_SENTENCE_UNIQUE_INDEX


def _normalize_semantic_text(value: str) -> str:
    """Normalize text for semantic duplicate comparison."""

    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split()).casefold()


def get_active_collocation_by_id(
    session: Session,
    collocation_id: int,
) -> Collocation | None:
    """Get an active collocation by its ID."""

    statement = select(Collocation).where(
        Collocation.id == collocation_id,
        col(Collocation.is_deleted).is_(False),
    )

    return session.exec(statement).first()


def get_collocation_by_id_including_deleted(
    session: Session,
    collocation_id: int,
) -> Collocation | None:
    """Get a collocation by its ID, including deleted ones."""

    return session.get(Collocation, collocation_id)


def get_active_example_sentence_by_id(
    session: Session,
    example_sentence_id: int,
) -> ExampleSentence | None:
    """Get an active example sentence by its ID."""

    statement = select(ExampleSentence).where(
        ExampleSentence.id == example_sentence_id,
        col(ExampleSentence.is_deleted).is_(False),
    )

    return session.exec(statement).first()


def get_example_sentence_by_id_including_deleted(
    session: Session,
    example_sentence_id: int,
) -> ExampleSentence | None:
    """Get an example sentence by its ID, including deleted ones."""

    return session.get(ExampleSentence, example_sentence_id)


def get_active_collocations_for_item(
    session: Session,
    vocabulary_item_id: int,
) -> list[Collocation]:
    """Get active collocations for an item in display order."""

    statement = (
        select(Collocation)
        .where(
            Collocation.vocabulary_item_id == vocabulary_item_id,
            col(Collocation.is_deleted).is_(False),
        )
        .order_by(
            Collocation.position.asc(),
            Collocation.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_active_example_sentences_for_item(
    session: Session,
    vocabulary_item_id: int,
) -> list[ExampleSentence]:
    """Get active examples for an item in display order."""

    statement = (
        select(ExampleSentence)
        .where(
            ExampleSentence.vocabulary_item_id == vocabulary_item_id,
            col(ExampleSentence.is_deleted).is_(False),
        )
        .order_by(
            ExampleSentence.position.asc(),
            ExampleSentence.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_active_collocations_for_items(
    session: Session,
    vocabulary_item_ids: Sequence[int],
) -> list[Collocation]:
    """Get active collocations for multiple items without N+1 queries."""

    if not vocabulary_item_ids:
        return []

    statement = (
        select(Collocation)
        .where(
            col(Collocation.vocabulary_item_id).in_(vocabulary_item_ids),
            col(Collocation.is_deleted).is_(False),
        )
        .order_by(
            Collocation.vocabulary_item_id.asc(),
            Collocation.position.asc(),
            Collocation.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_active_example_sentences_for_items(
    session: Session,
    vocabulary_item_ids: Sequence[int],
) -> list[ExampleSentence]:
    """Get active examples for multiple items without N+1 queries."""

    if not vocabulary_item_ids:
        return []

    statement = (
        select(ExampleSentence)
        .where(
            col(ExampleSentence.vocabulary_item_id).in_(
                vocabulary_item_ids
            ),
            col(ExampleSentence.is_deleted).is_(False),
        )
        .order_by(
            ExampleSentence.vocabulary_item_id.asc(),
            ExampleSentence.position.asc(),
            ExampleSentence.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_all_collocations_for_items_as_admin(
    session: Session,
    vocabulary_item_ids: Sequence[int],
) -> list[Collocation]:
    """Get collocations for multiple items, including deleted records."""

    if not vocabulary_item_ids:
        return []

    statement = (
        select(Collocation)
        .where(
            col(Collocation.vocabulary_item_id).in_(vocabulary_item_ids)
        )
        .order_by(
            Collocation.vocabulary_item_id.asc(),
            Collocation.position.asc(),
            Collocation.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_all_example_sentences_for_items_as_admin(
    session: Session,
    vocabulary_item_ids: Sequence[int],
) -> list[ExampleSentence]:
    """Get examples for multiple items, including deleted records."""

    if not vocabulary_item_ids:
        return []

    statement = (
        select(ExampleSentence)
        .where(
            col(ExampleSentence.vocabulary_item_id).in_(
                vocabulary_item_ids
            )
        )
        .order_by(
            ExampleSentence.vocabulary_item_id.asc(),
            ExampleSentence.position.asc(),
            ExampleSentence.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_active_examples_for_collocation(
    session: Session,
    collocation_id: int,
) -> list[ExampleSentence]:
    """Get active examples linked to a collocation."""

    statement = (
        select(ExampleSentence)
        .where(
            ExampleSentence.collocation_id == collocation_id,
            col(ExampleSentence.is_deleted).is_(False),
        )
        .order_by(
            ExampleSentence.position.asc(),
            ExampleSentence.id.asc(),
        )
    )

    return session.exec(statement).all()


def get_collocations_for_admin(
    session: Session,
    include_deleted: bool = False,
    vocabulary_item_id: int | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Collocation]:
    """Get collocations for administrators with optional filters."""

    statement = select(Collocation)

    if not include_deleted:
        statement = statement.where(
            col(Collocation.is_deleted).is_(False)
        )

    if vocabulary_item_id is not None:
        statement = statement.where(
            Collocation.vocabulary_item_id == vocabulary_item_id
        )

    if query is not None:
        normalized_query = _normalize_semantic_text(query)
        if normalized_query:
            statement = statement.where(
                col(Collocation.normalized_phrase).contains(
                    normalized_query,
                    autoescape=True,
                )
            )

    statement = (
        statement
        .order_by(Collocation.created_at.desc(), Collocation.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def get_example_sentences_for_admin(
    session: Session,
    include_deleted: bool = False,
    vocabulary_item_id: int | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ExampleSentence]:
    """Get example sentences for administrators with optional filters."""

    statement = select(ExampleSentence)

    if not include_deleted:
        statement = statement.where(
            col(ExampleSentence.is_deleted).is_(False)
        )

    if vocabulary_item_id is not None:
        statement = statement.where(
            ExampleSentence.vocabulary_item_id == vocabulary_item_id
        )

    if query is not None:
        normalized_query = _normalize_semantic_text(query)
        if normalized_query:
            statement = statement.where(
                col(ExampleSentence.normalized_sentence).contains(
                    normalized_query,
                    autoescape=True,
                )
            )

    statement = (
        statement
        .order_by(
            ExampleSentence.created_at.desc(),
            ExampleSentence.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


def _get_next_collocation_position(
    session: Session,
    vocabulary_item_id: int,
) -> int:
    """Get the next position for a collocation in an item."""

    statement = (
        select(Collocation.position)
        .where(
            Collocation.vocabulary_item_id == vocabulary_item_id,
            col(Collocation.is_deleted).is_(False),
        )
        .order_by(Collocation.position.desc())
        .limit(1)
    )

    highest_position = session.exec(statement).first()
    return (highest_position or 0) + 1


def _get_next_example_sentence_position(
    session: Session,
    vocabulary_item_id: int,
) -> int:
    """Get the next position for an example sentence in an item."""

    statement = (
        select(ExampleSentence.position)
        .where(
            ExampleSentence.vocabulary_item_id == vocabulary_item_id,
            col(ExampleSentence.is_deleted).is_(False),
        )
        .order_by(ExampleSentence.position.desc())
        .limit(1)
    )

    highest_position = session.exec(statement).first()
    return (highest_position or 0) + 1


def get_active_collocation_by_normalized_phrase(
    session: Session,
    vocabulary_item_id: int,
    normalized_phrase: str,
    exclude_collocation_id: int | None = None,
) -> Collocation | None:
    """Find an active collocation with an equivalent phrase."""

    statement = select(Collocation).where(
        Collocation.vocabulary_item_id == vocabulary_item_id,
        Collocation.normalized_phrase == normalized_phrase,
        col(Collocation.is_deleted).is_(False),
    )

    if exclude_collocation_id is not None:
        statement = statement.where(
            Collocation.id != exclude_collocation_id
        )

    return session.exec(statement).first()


def _ensure_collocation_is_not_duplicate(
    session: Session,
    vocabulary_item_id: int,
    normalized_phrase: str,
    exclude_collocation_id: int | None = None,
) -> None:
    """Raise a conflict when an equivalent active collocation exists."""

    duplicate = get_active_collocation_by_normalized_phrase(
        session=session,
        vocabulary_item_id=vocabulary_item_id,
        normalized_phrase=normalized_phrase,
        exclude_collocation_id=exclude_collocation_id,
    )

    if duplicate is not None:
        raise CollocationAlreadyExistsError()


def get_active_example_by_normalized_sentence(
    session: Session,
    vocabulary_item_id: int,
    normalized_sentence: str,
    exclude_example_sentence_id: int | None = None,
) -> ExampleSentence | None:
    """Find an active example with an equivalent sentence."""

    statement = select(ExampleSentence).where(
        ExampleSentence.vocabulary_item_id == vocabulary_item_id,
        ExampleSentence.normalized_sentence == normalized_sentence,
        col(ExampleSentence.is_deleted).is_(False),
    )

    if exclude_example_sentence_id is not None:
        statement = statement.where(
            ExampleSentence.id != exclude_example_sentence_id
        )

    return session.exec(statement).first()


def _ensure_example_sentence_is_not_duplicate(
    session: Session,
    vocabulary_item_id: int,
    normalized_sentence: str,
    exclude_example_sentence_id: int | None = None,
) -> None:
    """Raise a conflict when an equivalent active example exists."""

    duplicate = get_active_example_by_normalized_sentence(
        session=session,
        vocabulary_item_id=vocabulary_item_id,
        normalized_sentence=normalized_sentence,
        exclude_example_sentence_id=exclude_example_sentence_id,
    )

    if duplicate is not None:
        raise ExampleSentenceAlreadyExistsError()


def _validate_collocation_for_item(
    session: Session,
    collocation_id: int,
    vocabulary_item_id: int,
) -> Collocation:
    """Return an active collocation belonging to the specified item."""

    collocation = get_active_collocation_by_id(
        session=session,
        collocation_id=collocation_id,
    )

    if collocation is None:
        raise CollocationNotFoundError()

    if collocation.vocabulary_item_id != vocabulary_item_id:
        raise CollocationDoesNotBelongToItemError()

    return collocation


def create_collocation(
    session: Session,
    collocation_create: CollocationCreate,
    vocabulary_item_id: int,
) -> Collocation:
    """Create a collocation for a vocabulary item."""

    normalized_phrase = _normalize_semantic_text(
        collocation_create.phrase
    )
    _ensure_collocation_is_not_duplicate(
        session=session,
        vocabulary_item_id=vocabulary_item_id,
        normalized_phrase=normalized_phrase,
    )

    collocation = Collocation(
        vocabulary_item_id=vocabulary_item_id,
        phrase=collocation_create.phrase,
        normalized_phrase=normalized_phrase,
        english_meaning=collocation_create.english_meaning,
        vietnamese_meaning=collocation_create.vietnamese_meaning,
        note=collocation_create.note,
        position=_get_next_collocation_position(
            session=session,
            vocabulary_item_id=vocabulary_item_id,
        ),
    )

    try:
        session.add(collocation)
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_collocation_phrase_conflict(error):
            raise CollocationAlreadyExistsError() from error

        logger.exception(
            "Failed to create a collocation for vocabulary item %s.",
            vocabulary_item_id,
        )
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to create a collocation for vocabulary item %s.",
            vocabulary_item_id,
        )
        raise

    session.refresh(collocation)
    return collocation


def update_collocation(
    session: Session,
    collocation: Collocation,
    collocation_update: CollocationUpdate,
) -> Collocation:
    """Partially update a persisted, active collocation."""

    if collocation.id is None:
        raise RuntimeError("Cannot update a collocation without an ID.")

    update_data = collocation_update.model_dump(exclude_unset=True)

    if "phrase" in collocation_update.model_fields_set:
        phrase = collocation_update.phrase
        if phrase is None:
            raise RuntimeError("Validated phrase cannot be None.")

        normalized_phrase = _normalize_semantic_text(phrase)
        if normalized_phrase != collocation.normalized_phrase:
            _ensure_collocation_is_not_duplicate(
                session=session,
                vocabulary_item_id=collocation.vocabulary_item_id,
                normalized_phrase=normalized_phrase,
                exclude_collocation_id=collocation.id,
            )

        update_data["normalized_phrase"] = normalized_phrase

    collocation.sqlmodel_update(update_data)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_collocation_phrase_conflict(error):
            raise CollocationAlreadyExistsError() from error

        logger.exception(
            "Failed to update collocation %s.",
            collocation.id,
        )
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to update collocation %s.",
            collocation.id,
        )
        raise

    session.refresh(collocation)
    return collocation


def delete_collocation(
    session: Session,
    collocation: Collocation,
) -> None:
    """Soft-delete a collocation and its linked active examples."""

    if collocation.id is None:
        raise RuntimeError("Cannot delete a collocation without an ID.")

    deleted_at = utc_now()

    try:
        examples = get_active_examples_for_collocation(
            session=session,
            collocation_id=collocation.id,
        )

        collocation.is_deleted = True
        collocation.deleted_at = deleted_at

        for example in examples:
            example.is_deleted = True
            example.deleted_at = deleted_at

        session.commit()
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to delete collocation %s.",
            collocation.id,
        )
        raise


def create_example_sentence(
    session: Session,
    example_sentence_create: ExampleSentenceCreate,
    vocabulary_item_id: int,
) -> ExampleSentence:
    """Create an example sentence for a vocabulary item."""

    collocation_id = example_sentence_create.collocation_id
    if collocation_id is not None:
        _validate_collocation_for_item(
            session=session,
            collocation_id=collocation_id,
            vocabulary_item_id=vocabulary_item_id,
        )

    normalized_sentence = _normalize_semantic_text(
        example_sentence_create.sentence
    )
    _ensure_example_sentence_is_not_duplicate(
        session=session,
        vocabulary_item_id=vocabulary_item_id,
        normalized_sentence=normalized_sentence,
    )

    example_sentence = ExampleSentence(
        vocabulary_item_id=vocabulary_item_id,
        collocation_id=collocation_id,
        sentence=example_sentence_create.sentence,
        normalized_sentence=normalized_sentence,
        vietnamese_meaning=example_sentence_create.vietnamese_meaning,
        note=example_sentence_create.note,
        position=_get_next_example_sentence_position(
            session=session,
            vocabulary_item_id=vocabulary_item_id,
        ),
    )

    try:
        session.add(example_sentence)
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_example_sentence_conflict(error):
            raise ExampleSentenceAlreadyExistsError() from error

        logger.exception(
            "Failed to create an example for vocabulary item %s.",
            vocabulary_item_id,
        )
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to create an example for vocabulary item %s.",
            vocabulary_item_id,
        )
        raise

    session.refresh(example_sentence)
    return example_sentence


def update_example_sentence(
    session: Session,
    example_sentence: ExampleSentence,
    example_sentence_update: ExampleSentenceUpdate,
) -> ExampleSentence:
    """Partially update a persisted, active example sentence."""

    if example_sentence.id is None:
        raise RuntimeError(
            "Cannot update an example sentence without an ID."
        )

    update_data = example_sentence_update.model_dump(exclude_unset=True)

    if "collocation_id" in example_sentence_update.model_fields_set:
        collocation_id = example_sentence_update.collocation_id
        if collocation_id is not None:
            _validate_collocation_for_item(
                session=session,
                collocation_id=collocation_id,
                vocabulary_item_id=example_sentence.vocabulary_item_id,
            )

    if "sentence" in example_sentence_update.model_fields_set:
        sentence = example_sentence_update.sentence
        if sentence is None:
            raise RuntimeError("Validated sentence cannot be None.")

        normalized_sentence = _normalize_semantic_text(sentence)
        if normalized_sentence != example_sentence.normalized_sentence:
            _ensure_example_sentence_is_not_duplicate(
                session=session,
                vocabulary_item_id=example_sentence.vocabulary_item_id,
                normalized_sentence=normalized_sentence,
                exclude_example_sentence_id=example_sentence.id,
            )

        update_data["normalized_sentence"] = normalized_sentence

    example_sentence.sqlmodel_update(update_data)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        if _is_example_sentence_conflict(error):
            raise ExampleSentenceAlreadyExistsError() from error

        logger.exception(
            "Failed to update example sentence %s.",
            example_sentence.id,
        )
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to update example sentence %s.",
            example_sentence.id,
        )
        raise

    session.refresh(example_sentence)
    return example_sentence


def delete_example_sentence(
    session: Session,
    example_sentence: ExampleSentence,
) -> None:
    """Soft-delete a persisted, active example sentence."""

    if example_sentence.id is None:
        raise RuntimeError(
            "Cannot delete an example sentence without an ID."
        )

    example_sentence.is_deleted = True
    example_sentence.deleted_at = utc_now()

    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.exception(
            "Failed to delete example sentence %s.",
            example_sentence.id,
        )
        raise


def mark_content_deleted_for_items(
    session: Session,
    vocabulary_item_ids: Sequence[int],
    deleted_at: datetime,
) -> None:
    """Mark active content for multiple items deleted without committing."""

    if not vocabulary_item_ids:
        return

    collocations = get_active_collocations_for_items(
        session=session,
        vocabulary_item_ids=vocabulary_item_ids,
    )
    examples = get_active_example_sentences_for_items(
        session=session,
        vocabulary_item_ids=vocabulary_item_ids,
    )

    for collocation in collocations:
        collocation.is_deleted = True
        collocation.deleted_at = deleted_at

    for example in examples:
        example.is_deleted = True
        example.deleted_at = deleted_at


def mark_content_deleted_for_item(
    session: Session,
    vocabulary_item_id: int,
    deleted_at: datetime,
) -> None:
    """Mark active content for one item deleted without committing."""

    mark_content_deleted_for_items(
        session=session,
        vocabulary_item_ids=[vocabulary_item_id],
        deleted_at=deleted_at,
    )
