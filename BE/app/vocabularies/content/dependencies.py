from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import AdminUserDep, CurrentUserDep
from app.database.databases import SessionDep
from app.vocabularies.content.exceptions import (
    CollocationNotFoundError,
    ExampleSentenceNotFoundError,
)
from app.vocabularies.content.models import Collocation, ExampleSentence
from app.vocabularies.content.service import (
    get_active_collocation_by_id,
    get_active_example_sentence_by_id,
    get_collocation_by_id_including_deleted,
    get_example_sentence_by_id_including_deleted,
)
from app.vocabularies.dependencies import (
    get_owned_vocabulary_item_or_404,
)
from app.vocabularies.exceptions import VocabularyItemNotFoundError


def get_owned_collocation_or_404(
    collocation_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Collocation:
    """Resolve an active collocation owned by the current user."""

    collocation = get_active_collocation_by_id(
        session=session,
        collocation_id=collocation_id,
    )
    if collocation is None:
        raise CollocationNotFoundError()

    try:
        get_owned_vocabulary_item_or_404(
            vocabulary_item_id=collocation.vocabulary_item_id,
            session=session,
            current_user=current_user,
        )
    except VocabularyItemNotFoundError as error:
        raise CollocationNotFoundError() from error

    return collocation


OwnedCollocationDep = Annotated[
    Collocation,
    Depends(get_owned_collocation_or_404),
]


def get_owned_example_sentence_or_404(
    example_sentence_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ExampleSentence:
    """Resolve an active example sentence owned by the current user."""

    example_sentence = get_active_example_sentence_by_id(
        session=session,
        example_sentence_id=example_sentence_id,
    )
    if example_sentence is None:
        raise ExampleSentenceNotFoundError()

    try:
        get_owned_vocabulary_item_or_404(
            vocabulary_item_id=example_sentence.vocabulary_item_id,
            session=session,
            current_user=current_user,
        )
    except VocabularyItemNotFoundError as error:
        raise ExampleSentenceNotFoundError() from error

    return example_sentence


OwnedExampleSentenceDep = Annotated[
    ExampleSentence,
    Depends(get_owned_example_sentence_or_404),
]


def get_admin_collocation_or_404(
    collocation_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> Collocation:
    """Resolve a collocation for admin audit, including deleted records."""

    collocation = get_collocation_by_id_including_deleted(
        session=session,
        collocation_id=collocation_id,
    )
    if collocation is None:
        raise CollocationNotFoundError()

    return collocation


AdminCollocationDep = Annotated[
    Collocation,
    Depends(get_admin_collocation_or_404),
]


def get_active_admin_collocation_or_404(
    collocation_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> Collocation:
    """Resolve an active collocation for an admin command."""

    collocation = get_active_collocation_by_id(
        session=session,
        collocation_id=collocation_id,
    )
    if collocation is None:
        raise CollocationNotFoundError()

    return collocation


ActiveAdminCollocationDep = Annotated[
    Collocation,
    Depends(get_active_admin_collocation_or_404),
]


def get_admin_example_sentence_or_404(
    example_sentence_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> ExampleSentence:
    """Resolve an example sentence for admin audit, including deleted."""

    example_sentence = get_example_sentence_by_id_including_deleted(
        session=session,
        example_sentence_id=example_sentence_id,
    )
    if example_sentence is None:
        raise ExampleSentenceNotFoundError()

    return example_sentence


AdminExampleSentenceDep = Annotated[
    ExampleSentence,
    Depends(get_admin_example_sentence_or_404),
]


def get_active_admin_example_sentence_or_404(
    example_sentence_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> ExampleSentence:
    """Resolve an active example sentence for an admin command."""

    example_sentence = get_active_example_sentence_by_id(
        session=session,
        example_sentence_id=example_sentence_id,
    )
    if example_sentence is None:
        raise ExampleSentenceNotFoundError()

    return example_sentence


ActiveAdminExampleSentenceDep = Annotated[
    ExampleSentence,
    Depends(get_active_admin_example_sentence_or_404),
]
