from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUserDep
from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.vocabularies import service as vocabulary_service
from app.vocabularies.dependencies import (
    ActiveAdminVocabularyDep,
    AdminVocabularyDep,
)
from app.vocabularies.presenters import build_vocabulary_detail_response
from app.vocabularies.schemas import (
    VocabularyDetailResponse,
    VocabularyListResponse,
)


router = APIRouter(
    prefix="/admin/vocabularies",
    tags=["Admin - Vocabularies"],
)


@router.get(
    "",
    response_model=BaseResponse[list[VocabularyListResponse]],
    summary="List vocabularies as an administrator",
)
def get_vocabularies_as_admin(
    session: SessionDep,
    _admin: AdminUserDep,
    include_deleted: bool = Query(default=False),
    deck_id: int | None = Query(default=None, ge=1),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BaseResponse[list[VocabularyListResponse]]:
    vocabularies = vocabulary_service.get_vocabularies_for_admin(
        session=session,
        include_deleted=include_deleted,
        deck_id=deck_id,
        query=q,
        limit=limit,
        offset=offset,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabularies retrieved successfully.",
        result=vocabularies,
    )


@router.get(
    "/{vocabulary_id}",
    response_model=BaseResponse[VocabularyDetailResponse],
    summary="Get a vocabulary by ID as an administrator",
)
def get_vocabulary_by_id_as_admin(
    vocabulary_id: int,
    session: SessionDep,
    vocabulary: AdminVocabularyDep,
) -> BaseResponse[VocabularyDetailResponse]:
    items = vocabulary_service.get_all_items_in_vocabulary_including_deleted(
        session=session,
        vocabulary_id=vocabulary_id,
    )
    result = build_vocabulary_detail_response(vocabulary, items)

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary retrieved successfully.",
        result=result,
    )


@router.delete(
    "/{vocabulary_id}",
    response_model=BaseResponse[None],
    summary="Delete a vocabulary as an administrator",
)
def delete_vocabulary_as_admin(
    session: SessionDep,
    vocabulary: ActiveAdminVocabularyDep,
) -> BaseResponse[None]:
    vocabulary_service.delete_vocabulary(
        session=session,
        vocabulary=vocabulary,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Vocabulary deleted successfully.",
    )
