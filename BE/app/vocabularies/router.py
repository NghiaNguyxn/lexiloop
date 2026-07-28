from fastapi import APIRouter, Query, status

from app.vocabularies.dependencies import (
    OwnedVocabularyDep,
    OwnedVocabularyItemDep,
    ReadableVocabularyDep,
)
from app.vocabularies.schemas import (
    VocabularyCreate,
    VocabularyItemUpdate,
    VocabularyListResponse,
    VocabularyDetailResponse,
    VocabularyItemCreate,
    VocabularyItemResponse,
    VocabularyUpdate,
)
from app.vocabularies import service as vocabulary_service
from app.vocabularies.content import service as content_service
from app.vocabularies.presenters import build_vocabulary_detail_response
from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.decks.dependencies import ReadableDeckDep, OwnedDeckDep


router = APIRouter(tags=["Vocabularies"])


@router.get(
    "/vocabularies/{vocabulary_id}",
    response_model=BaseResponse[VocabularyDetailResponse],
    summary="Get a vocabulary by ID",
)
def get_vocabulary(
    session: SessionDep,
    vocabulary: ReadableVocabularyDep,
    vocabulary_id: int,
) -> BaseResponse[VocabularyDetailResponse]:
    items = vocabulary_service.get_all_active_items_in_vocabulary(
        session=session,
        vocabulary_id=vocabulary_id,
    )
    item_ids = [item.id for item in items if item.id is not None]
    collocations = content_service.get_active_collocations_for_items(
        session=session,
        vocabulary_item_ids=item_ids,
    )
    example_sentences = (
        content_service.get_active_example_sentences_for_items(
            session=session,
            vocabulary_item_ids=item_ids,
        )
    )
    result = build_vocabulary_detail_response(
        vocabulary=vocabulary,
        items=items,
        collocations=collocations,
        example_sentences=example_sentences,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary retrieved successfully.",
        result=result,
    )


@router.get(
    "/decks/{deck_id}/vocabularies",
    response_model=BaseResponse[list[VocabularyListResponse]],
    summary="Get all vocabularies in a readable deck by deck ID",
)
def get_vocabularies_in_deck(
    session: SessionDep,
    deck_id: int,
    _deck: ReadableDeckDep,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of vocabularies to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of vocabularies to skip.",
    ),
) -> BaseResponse[list[VocabularyListResponse]]:
    vocabularies = vocabulary_service.get_active_vocabularies_in_deck(
        session=session,
        deck_id=deck_id,
        limit=limit,
        offset=offset,
    )
    meaning_counts = vocabulary_service.get_active_meaning_counts(
        session=session,
        vocabulary_ids=[
            vocabulary.id
            for vocabulary in vocabularies
            if vocabulary.id is not None
        ],
    )
    result = [
        VocabularyListResponse.model_validate(vocabulary).model_copy(
            update={
                "meaning_count": meaning_counts.get(vocabulary.id, 0),
            },
        )
        for vocabulary in vocabularies
    ]

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabularies retrieved successfully.",
        result=result,
    )


@router.post(
    "/decks/{deck_id}/vocabularies",
    response_model=BaseResponse[VocabularyDetailResponse],
    summary="Create a new vocabulary in an owned deck by deck ID",
    status_code=status.HTTP_201_CREATED,
)
def create_vocabulary(
    session: SessionDep,
    deck_id: int,
    _deck: OwnedDeckDep,
    vocabulary_create: VocabularyCreate,
) -> BaseResponse[VocabularyDetailResponse]:
    vocabulary = vocabulary_service.create_vocabulary(
        session=session,
        deck_id=deck_id,
        vocabulary_create=vocabulary_create,
    )

    items = vocabulary_service.get_all_active_items_in_vocabulary(
        session=session,
        vocabulary_id=vocabulary.id,
    )

    result = build_vocabulary_detail_response(
        vocabulary=vocabulary,
        items=items,
        collocations=[],
        example_sentences=[],
    )

    return create_success_response(
        code=status.HTTP_201_CREATED,
        message="Vocabulary created successfully.",
        result=result,
    )


@router.patch(
    "/vocabularies/{vocabulary_id}",
    response_model=BaseResponse[VocabularyListResponse],
    summary="Update an existing vocabulary by ID",
)
def update_vocabulary(
    session: SessionDep,
    vocabulary: OwnedVocabularyDep,
    vocabulary_update: VocabularyUpdate,
) -> BaseResponse[VocabularyListResponse]:
    vocabulary = vocabulary_service.update_vocabulary(
        session=session,
        vocabulary=vocabulary,
        vocabulary_update=vocabulary_update,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary updated successfully.",
        result=vocabulary,
    )


@router.delete(
    "/vocabularies/{vocabulary_id}",
    response_model=BaseResponse[None],
    summary="Delete an existing vocabulary by ID",
)
def delete_vocabulary(
    session: SessionDep,
    vocabulary: OwnedVocabularyDep,
) -> BaseResponse[None]:
    vocabulary_service.delete_vocabulary(
        session=session,
        vocabulary=vocabulary,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary deleted successfully.",
    )


@router.post(
    "/vocabularies/{vocabulary_id}/items",
    response_model=BaseResponse[VocabularyItemResponse],
    summary="Add a new item to an existing vocabulary by ID",
    status_code=status.HTTP_201_CREATED,
)
def add_vocabulary_item(
    session: SessionDep,
    vocabulary: OwnedVocabularyDep,
    item_create: VocabularyItemCreate,
) -> BaseResponse[VocabularyItemResponse]:
    item = vocabulary_service.create_vocabulary_item(
        session=session,
        vocabulary=vocabulary,
        item_create=item_create,
    )

    return create_success_response(
        code=status.HTTP_201_CREATED,
        message="Vocabulary item added successfully.",
        result=item,
    )


@router.patch(
    "/vocabulary-items/{vocabulary_item_id}",
    response_model=BaseResponse[VocabularyItemResponse],
    summary="Update an existing vocabulary item by ID",
)
def update_vocabulary_item(
    session: SessionDep,
    item: OwnedVocabularyItemDep,
    item_update: VocabularyItemUpdate,
) -> BaseResponse[VocabularyItemResponse]:
    updated_item = vocabulary_service.update_vocabulary_item(
        session=session,
        item=item,
        item_update=item_update,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary item updated successfully.",
        result=updated_item,
    )


@router.delete(
    "/vocabulary-items/{vocabulary_item_id}",
    response_model=BaseResponse[None],
    summary="Delete an existing vocabulary item by ID",
)
def delete_vocabulary_item(
    session: SessionDep,
    item: OwnedVocabularyItemDep,
) -> BaseResponse[None]:
    vocabulary_service.delete_vocabulary_item(
        session=session,
        item=item,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary item deleted successfully.",
    )
