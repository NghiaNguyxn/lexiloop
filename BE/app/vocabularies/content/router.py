from fastapi import APIRouter, status

from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.vocabularies.content import service as content_service
from app.vocabularies.content.dependencies import (
    OwnedCollocationDep,
    OwnedExampleSentenceDep,
)
from app.vocabularies.content.schemas import (
    CollocationCreate,
    CollocationResponse,
    CollocationUpdate,
    ExampleSentenceCreate,
    ExampleSentenceResponse,
    ExampleSentenceUpdate,
)
from app.vocabularies.dependencies import OwnedVocabularyItemDep


router = APIRouter(tags=["Vocabulary Content"])


@router.post(
    "/vocabulary-items/{vocabulary_item_id}/collocations",
    response_model=BaseResponse[CollocationResponse],
    summary="Create a collocation for a vocabulary item",
    status_code=status.HTTP_201_CREATED,
)
def create_collocation(
    session: SessionDep,
    vocabulary_item: OwnedVocabularyItemDep,
    collocation_create: CollocationCreate,
) -> BaseResponse[CollocationResponse]:
    if vocabulary_item.id is None:
        raise RuntimeError(
            "Persisted vocabulary item does not have an ID."
        )

    collocation = content_service.create_collocation(
        session=session,
        vocabulary_item_id=vocabulary_item.id,
        collocation_create=collocation_create,
    )

    return create_success_response(
        code=status.HTTP_201_CREATED,
        message="Collocation created successfully.",
        result=collocation,
    )


@router.patch(
    "/vocabulary-collocations/{collocation_id}",
    response_model=BaseResponse[CollocationResponse],
    summary="Update a collocation by ID",
)
def update_collocation(
    session: SessionDep,
    collocation: OwnedCollocationDep,
    collocation_update: CollocationUpdate,
) -> BaseResponse[CollocationResponse]:
    updated_collocation = content_service.update_collocation(
        session=session,
        collocation=collocation,
        collocation_update=collocation_update,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Collocation updated successfully.",
        result=updated_collocation,
    )


@router.delete(
    "/vocabulary-collocations/{collocation_id}",
    response_model=BaseResponse[None],
    summary="Delete a collocation by ID",
)
def delete_collocation(
    session: SessionDep,
    collocation: OwnedCollocationDep,
) -> BaseResponse[None]:
    content_service.delete_collocation(
        session=session,
        collocation=collocation,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Collocation deleted successfully.",
    )


@router.post(
    "/vocabulary-items/{vocabulary_item_id}/example-sentences",
    response_model=BaseResponse[ExampleSentenceResponse],
    summary="Create an example sentence for a vocabulary item",
    status_code=status.HTTP_201_CREATED,
)
def create_example_sentence(
    session: SessionDep,
    vocabulary_item: OwnedVocabularyItemDep,
    example_sentence_create: ExampleSentenceCreate,
) -> BaseResponse[ExampleSentenceResponse]:
    if vocabulary_item.id is None:
        raise RuntimeError(
            "Persisted vocabulary item does not have an ID."
        )

    example_sentence = content_service.create_example_sentence(
        session=session,
        vocabulary_item_id=vocabulary_item.id,
        example_sentence_create=example_sentence_create,
    )

    return create_success_response(
        code=status.HTTP_201_CREATED,
        message="Example sentence created successfully.",
        result=example_sentence,
    )


@router.patch(
    "/example-sentences/{example_sentence_id}",
    response_model=BaseResponse[ExampleSentenceResponse],
    summary="Update an example sentence by ID",
)
def update_example_sentence(
    session: SessionDep,
    example_sentence: OwnedExampleSentenceDep,
    example_sentence_update: ExampleSentenceUpdate,
) -> BaseResponse[ExampleSentenceResponse]:
    updated_example_sentence = content_service.update_example_sentence(
        session=session,
        example_sentence=example_sentence,
        example_sentence_update=example_sentence_update,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Example sentence updated successfully.",
        result=updated_example_sentence,
    )


@router.delete(
    "/example-sentences/{example_sentence_id}",
    response_model=BaseResponse[None],
    summary="Delete an example sentence by ID",
)
def delete_example_sentence(
    session: SessionDep,
    example_sentence: OwnedExampleSentenceDep,
) -> BaseResponse[None]:
    content_service.delete_example_sentence(
        session=session,
        example_sentence=example_sentence,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Example sentence deleted successfully.",
    )
