from app.vocabularies.models import Vocabulary, VocabularyItem
from app.vocabularies.schemas import VocabularyDetailResponse


def build_vocabulary_detail_response(
    vocabulary: Vocabulary,
    items: list[VocabularyItem],
) -> VocabularyDetailResponse:
    """Build a nested vocabulary response from persisted models."""

    if vocabulary.id is None:
        raise RuntimeError("Cannot build a response for a vocabulary without an ID.")
    if vocabulary.created_at is None or vocabulary.updated_at is None:
        raise RuntimeError("Persisted vocabulary timestamps are missing.")

    return VocabularyDetailResponse(
        id=vocabulary.id,
        deck_id=vocabulary.deck_id,
        word=vocabulary.word,
        is_deleted=vocabulary.is_deleted,
        deleted_at=vocabulary.deleted_at,
        created_at=vocabulary.created_at,
        updated_at=vocabulary.updated_at,
        items=items,
    )
