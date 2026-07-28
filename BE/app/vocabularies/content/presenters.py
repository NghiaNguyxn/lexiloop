from collections import defaultdict

from app.vocabularies.content.models import (
    Collocation,
    ExampleSentence,
)
from app.vocabularies.content.schemas import (
    CollocationResponse,
    ExampleSentenceResponse,
)
from app.vocabularies.models import VocabularyItem
from app.vocabularies.schemas import (
    VocabularyItemContentResponse,
    VocabularyItemResponse,
)


def build_vocabulary_item_content_responses(
    items: list[VocabularyItem],
    collocations: list[Collocation],
    example_sentences: list[ExampleSentence],
) -> list[VocabularyItemContentResponse]:
    """Build nested item responses without performing database queries."""

    collocations_by_item: dict[int, list[CollocationResponse]] = (
        defaultdict(list)
    )
    for collocation in collocations:
        collocations_by_item[collocation.vocabulary_item_id].append(
            CollocationResponse.model_validate(collocation)
        )

    examples_by_item: dict[int, list[ExampleSentenceResponse]] = (
        defaultdict(list)
    )
    for example_sentence in example_sentences:
        examples_by_item[example_sentence.vocabulary_item_id].append(
            ExampleSentenceResponse.model_validate(example_sentence)
        )

    responses: list[VocabularyItemContentResponse] = []
    for item in items:
        if item.id is None:
            raise RuntimeError(
                "Cannot build a response for an item without an ID."
            )

        item_response = VocabularyItemResponse.model_validate(item)
        responses.append(
            VocabularyItemContentResponse(
                **item_response.model_dump(),
                collocations=collocations_by_item[item.id],
                example_sentences=examples_by_item[item.id],
            )
        )

    return responses
