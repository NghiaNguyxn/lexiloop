from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import AdminUserDep, CurrentUserDep
from app.database.databases import SessionDep
from app.decks.exceptions import DeckNotFoundError
from app.decks.models import Deck
from app.decks.service import (
    get_active_owned_deck_by_id,
    get_deck_by_id_including_deleted,
    get_readable_deck_by_id,
)


def get_readable_deck_or_404(deck_id: int, session: SessionDep, current_user: CurrentUserDep) -> Deck:
    deck = get_readable_deck_by_id(session=session, deck_id=deck_id, user_id=current_user.id)
    if deck is None:
        raise DeckNotFoundError()

    return deck

ReadableDeckDep = Annotated[Deck, Depends(get_readable_deck_or_404)]

def get_owned_deck_or_404(deck_id: int, session: SessionDep, current_user: CurrentUserDep) -> Deck:
    deck = get_active_owned_deck_by_id(session=session, deck_id=deck_id, user_id=current_user.id)
    if deck is None:
        raise DeckNotFoundError()

    return deck

OwnedDeckDep = Annotated[Deck, Depends(get_owned_deck_or_404)]


def get_admin_deck_or_404(
    deck_id: int,
    session: SessionDep,
    _admin: AdminUserDep,
) -> Deck:
    deck = get_deck_by_id_including_deleted(
        session=session,
        deck_id=deck_id,
    )
    if deck is None:
        raise DeckNotFoundError()

    return deck


AdminDeckDep = Annotated[Deck, Depends(get_admin_deck_or_404)]
