from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUserDep
from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.vocabularies.content import service as content_service
from app.vocabularies.content.dependencies import (
    ActiveAdminCollocationDep,
    ActiveAdminExampleSentenceDep,
    AdminCollocationDep,
    AdminExampleSentenceDep,
)
from app.vocabularies.content.schemas import (
    CollocationResponse,
    ExampleSentenceResponse,
)


router = APIRouter(tags=["Admin - Vocabulary Content"])


@router.get(
    "/admin/vocabulary-collocations",
    response_model=BaseResponse[list[CollocationResponse]],
    summary="List collocations as an administrator",
)
def get_collocations_as_admin(
    session: SessionDep,
    _admin: AdminUserDep,
    include_deleted: bool = Query(default=False),
    vocabulary_item_id: int | None = Query(default=None, ge=1),
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BaseResponse[list[CollocationResponse]]:
    collocations = content_service.get_collocations_for_admin(
        session=session,
        include_deleted=include_deleted,
        vocabulary_item_id=vocabulary_item_id,
        query=q,
        limit=limit,
        offset=offset,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Collocations retrieved successfully.",
        result=collocations,
    )


@router.get(
    "/admin/vocabulary-collocations/{collocation_id}",
    response_model=BaseResponse[CollocationResponse],
    summary="Get a collocation by ID as an administrator",
)
def get_collocation_as_admin(
    collocation: AdminCollocationDep,
) -> BaseResponse[CollocationResponse]:
    return create_success_response(
        code=status.HTTP_200_OK,
        message="Collocation retrieved successfully.",
        result=collocation,
    )


@router.delete(
    "/admin/vocabulary-collocations/{collocation_id}",
    response_model=BaseResponse[None],
    summary="Delete a collocation as an administrator",
)
def delete_collocation_as_admin(
    session: SessionDep,
    collocation: ActiveAdminCollocationDep,
) -> BaseResponse[None]:
    content_service.delete_collocation(
        session=session,
        collocation=collocation,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Collocation deleted successfully.",
    )


@router.get(
    "/admin/example-sentences",
    response_model=BaseResponse[list[ExampleSentenceResponse]],
    summary="List example sentences as an administrator",
)
def get_example_sentences_as_admin(
    session: SessionDep,
    _admin: AdminUserDep,
    include_deleted: bool = Query(default=False),
    vocabulary_item_id: int | None = Query(default=None, ge=1),
    q: str | None = Query(default=None, max_length=500),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BaseResponse[list[ExampleSentenceResponse]]:
    example_sentences = content_service.get_example_sentences_for_admin(
        session=session,
        include_deleted=include_deleted,
        vocabulary_item_id=vocabulary_item_id,
        query=q,
        limit=limit,
        offset=offset,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Example sentences retrieved successfully.",
        result=example_sentences,
    )


@router.get(
    "/admin/example-sentences/{example_sentence_id}",
    response_model=BaseResponse[ExampleSentenceResponse],
    summary="Get an example sentence by ID as an administrator",
)
def get_example_sentence_as_admin(
    example_sentence: AdminExampleSentenceDep,
) -> BaseResponse[ExampleSentenceResponse]:
    return create_success_response(
        code=status.HTTP_200_OK,
        message="Example sentence retrieved successfully.",
        result=example_sentence,
    )


@router.delete(
    "/admin/example-sentences/{example_sentence_id}",
    response_model=BaseResponse[None],
    summary="Delete an example sentence as an administrator",
)
def delete_example_sentence_as_admin(
    session: SessionDep,
    example_sentence: ActiveAdminExampleSentenceDep,
) -> BaseResponse[None]:
    content_service.delete_example_sentence(
        session=session,
        example_sentence=example_sentence,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Example sentence deleted successfully.",
    )
