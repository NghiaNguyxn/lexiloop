from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import AdminUserDep, CurrentUserDep
from app.database.databases import SessionDep
from app.decks.service import (
    get_active_owned_deck_by_id,
    get_readable_deck_by_id,
)
from app.vocabularies.exceptions import (
    VocabularyItemNotFoundError,
    VocabularyNotFoundError,
)
from app.vocabularies.models import Vocabulary, VocabularyItem
from app.vocabularies.service import (
    get_active_vocabulary_item_by_id,
    get_active_vocabulary_by_id,
    get_vocabulary_by_id_including_deleted,
)


def get_readable_vocabulary_or_404(
    vocabulary_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Vocabulary:
    vocabulary = get_active_vocabulary_by_id(
        session=session,
        vocabulary_id=vocabulary_id,
    )
    if vocabulary is None:
        raise VocabularyNotFoundError()

    deck = get_readable_deck_by_id(
        session=session,
        deck_id=vocabulary.deck_id,
        user_id=current_user.id,
    )
    if deck is None:
        raise VocabularyNotFoundError()

    return vocabulary


ReadableVocabularyDep = Annotated[
    Vocabulary,
    Depends(get_readable_vocabulary_or_404),
]


def get_owned_vocabulary_or_404(
    vocabulary_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Vocabulary:
    vocabulary = get_active_vocabulary_by_id(
        session=session,
        vocabulary_id=vocabulary_id,
    )
    if vocabulary is None:
        raise VocabularyNotFoundError()

    deck = get_active_owned_deck_by_id(
        session=session,
        deck_id=vocabulary.deck_id,
        user_id=current_user.id,
    )
    if deck is None:
        raise VocabularyNotFoundError()

    return vocabulary


OwnedVocabularyDep = Annotated[
    Vocabulary,
    Depends(get_owned_vocabulary_or_404),
]


def get_owned_vocabulary_item_or_404(
    vocabulary_item_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> VocabularyItem:
    vocabulary_item = get_active_vocabulary_item_by_id(
        session=session,
        vocabulary_item_id=vocabulary_item_id,
    )
    if vocabulary_item is None:
        raise VocabularyItemNotFoundError()

    vocabulary = get_active_vocabulary_by_id(
        session=session,
        vocabulary_id=vocabulary_item.vocabulary_id,
    )
    if vocabulary is None:
        raise VocabularyItemNotFoundError()

    deck = get_active_owned_deck_by_id(
        session=session,
        deck_id=vocabulary.deck_id,
        user_id=current_user.id,
    )
    if deck is None:
        raise VocabularyItemNotFoundError()

    return vocabulary_item


OwnedVocabularyItemDep = Annotated[
    VocabularyItem,
    Depends(get_owned_vocabulary_item_or_404),
]


def get_admin_vocabulary_or_404(
    vocabulary_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> Vocabulary:
    vocabulary = get_vocabulary_by_id_including_deleted(
        session=session,
        vocabulary_id=vocabulary_id,
    )
    if vocabulary is None:
        raise VocabularyNotFoundError()

    return vocabulary


AdminVocabularyDep = Annotated[
    Vocabulary,
    Depends(get_admin_vocabulary_or_404),
]


def get_active_admin_vocabulary_or_404(
    vocabulary_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> Vocabulary:
    vocabulary = get_active_vocabulary_by_id(
        session=session,
        vocabulary_id=vocabulary_id,
    )
    if vocabulary is None:
        raise VocabularyNotFoundError()

    return vocabulary


ActiveAdminVocabularyDep = Annotated[
    Vocabulary,
    Depends(get_active_admin_vocabulary_or_404),
]
