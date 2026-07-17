from fastapi import APIRouter, Query, status

from app.auth.dependencies import CurrentUserDep
from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.decks import service as deck_service
from app.decks.dependencies import ReadableDeckDep, OwnedDeckDep
from app.decks.schemas import DeckCreate, DeckUpdate, DeckResponse


router = APIRouter(prefix="/decks", tags=["Decks"])


@router.get(
    "/owned",
    response_model=BaseResponse[list[DeckResponse]],
    summary="Get all decks owned by the current user",
)
def get_owned_decks(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of decks to return."),
    offset: int = Query(default=0, ge=0, description="Number of decks to skip."),
) -> BaseResponse[list[DeckResponse]]:
    decks = deck_service.get_user_decks(
        session=session,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Owned decks retrieved successfully.",
        result=decks,
    )


@router.get(
    "/public",
    response_model=BaseResponse[list[DeckResponse]],
    summary="Get all public decks",
)
def get_public_decks(
    session: SessionDep,
    _current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of decks to return."),
    offset: int = Query(default=0, ge=0, description="Number of decks to skip."),
) -> BaseResponse[list[DeckResponse]]:
    decks = deck_service.get_public_decks(
        session=session,
        limit=limit,
        offset=offset
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Public decks retrieved successfully.",
        result=decks,
    )


@router.get(
    "/{deck_id}",
    response_model=BaseResponse[DeckResponse],
    summary="Get a owned or public deck by ID",
)
def get_deck_by_id(
    deck: ReadableDeckDep,
) -> BaseResponse[DeckResponse]:
    return create_success_response(
        code=status.HTTP_200_OK,
        message="Deck retrieved successfully.",
        result=deck,
    )


@router.post(
    "",
    response_model=BaseResponse[DeckResponse],
    summary="Create a new deck",
    status_code=status.HTTP_201_CREATED,
)
def create_deck(
    session: SessionDep,
    current_user: CurrentUserDep,
    deck_create: DeckCreate,
) -> BaseResponse[DeckResponse]:
    deck = deck_service.create_deck(
        session=session,
        deck_create=deck_create,
        user_id=current_user.id
    )

    return create_success_response(
        code=status.HTTP_201_CREATED,
        message="Deck created successfully.",
        result=deck,
    )


@router.patch(
    "/{deck_id}",
    response_model=BaseResponse[DeckResponse],
    summary="Update an existing deck",
)
def update_deck(
    session: SessionDep,
    deck_update: DeckUpdate,
    deck: OwnedDeckDep,
) -> BaseResponse[DeckResponse]:
    updated_deck = deck_service.update_deck(
        session=session,
        deck=deck,
        deck_update=deck_update
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Deck updated successfully.",
        result=updated_deck,
    )


@router.delete(
    "/{deck_id}",
    response_model=BaseResponse[None],
    summary="Delete an existing deck",
)
def delete_deck(
    session: SessionDep,
    deck: OwnedDeckDep,
) -> BaseResponse[None]:
    deck_service.delete_deck(
        session=session,
        deck=deck,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Deck deleted successfully.",
    )
