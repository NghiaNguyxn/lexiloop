from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUserDep
from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.decks import service as deck_service
from app.decks.dependencies import AdminDeckDep
from app.decks.schemas import DeckAdminResponse


router = APIRouter(prefix="/admin/decks", tags=["Admin - Decks"])


@router.get(
    "",
    response_model=BaseResponse[list[DeckAdminResponse]],
    summary="List decks as an administrator",
)
def get_decks_as_admin(
    session: SessionDep,
    _admin: AdminUserDep,
    include_deleted: bool = Query(default=False),
    user_id: int | None = Query(default=None, ge=1),
    is_public: bool | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BaseResponse[list[DeckAdminResponse]]:
    decks = deck_service.get_decks_for_admin(
        session=session,
        include_deleted=include_deleted,
        user_id=user_id,
        is_public=is_public,
        query=q,
        limit=limit,
        offset=offset,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Decks retrieved successfully.",
        result=decks,
    )


@router.get(
    "/{deck_id}",
    response_model=BaseResponse[DeckAdminResponse],
    summary="Get a deck by ID as an administrator",
)
def get_deck_by_id_as_admin(
    deck: AdminDeckDep,
) -> BaseResponse[DeckAdminResponse]:
    return create_success_response(
        code=status.HTTP_200_OK,
        message="Deck retrieved successfully.",
        result=deck,
    )
