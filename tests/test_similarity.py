from unittest.mock import AsyncMock, create_autospec
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.exceptions import LlmInvalidResponseError
from app.features.similarity.schemas import SimilarityFindRequest
from app.features.similarity.service import SimilarityService
from app.llm.base import ILlmProvider, SimilarityMatch, SimilarityResult
from tests.conftest import FIRST_CATEGORY_ID, SECOND_CATEGORY_ID


def test_similarity_request_rejects_empty_candidates(
    similarity_payload: dict,
) -> None:
    similarity_payload["existing_reports"] = []

    with pytest.raises(ValidationError):
        SimilarityFindRequest.model_validate(similarity_payload)


@pytest.mark.asyncio
async def test_similarity_service_sorts_provider_results(
    similarity_payload: dict,
) -> None:
    provider = create_autospec(ILlmProvider, instance=True)
    provider.find_similar_reports = AsyncMock(
        return_value=SimilarityResult(
            similar_reports=[
                SimilarityMatch(
                    report_id=UUID(SECOND_CATEGORY_ID),
                    similarity_score=0.35,
                    reasoning="Yalnizca genel konu benzerligi var.",
                ),
                SimilarityMatch(
                    report_id=UUID(FIRST_CATEGORY_ID),
                    similarity_score=0.93,
                    reasoning="Ayni konumdaki ayni su arizasini anlatiyor.",
                ),
            ]
        )
    )
    request = SimilarityFindRequest.model_validate(similarity_payload)

    response = await SimilarityService(provider).find_similar_reports(request)

    assert response.similar_reports[0].report_id == UUID(FIRST_CATEGORY_ID)
    assert response.similar_reports[0].similarity_score == 0.93


@pytest.mark.asyncio
async def test_similarity_service_rejects_unknown_report_id(
    similarity_payload: dict,
) -> None:
    provider = create_autospec(ILlmProvider, instance=True)
    provider.find_similar_reports = AsyncMock(
        return_value=SimilarityResult(
            similar_reports=[
                SimilarityMatch(
                    report_id=UUID("018f6f64-5f47-7e37-b7dc-2f9bc8f69d99"),
                    similarity_score=0.90,
                    reasoning="Gecersiz aday.",
                )
            ]
        )
    )
    request = SimilarityFindRequest.model_validate(similarity_payload)

    with pytest.raises(LlmInvalidResponseError):
        await SimilarityService(provider).find_similar_reports(request)
