from unittest.mock import AsyncMock, create_autospec

import pytest
from pydantic import ValidationError

from app.features.priority.schemas import PriorityScoreRequest, PriorityScoreResponse
from app.features.priority.service import PriorityService
from app.llm.base import ILlmProvider, PriorityResult, get_priority_for_score


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "Low"),
        (0.25, "Low"),
        (0.26, "Medium"),
        (0.50, "Medium"),
        (0.51, "High"),
        (0.75, "High"),
        (0.76, "Urgent"),
        (1.0, "Urgent"),
    ],
)
def test_priority_score_boundaries(score: float, expected: str) -> None:
    assert get_priority_for_score(score) == expected


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_priority_result_rejects_score_outside_range(score: float) -> None:
    with pytest.raises(ValidationError):
        PriorityResult(
            priority_score=score,
            suggested_priority="Low",
            reasoning="Geçersiz skor",
        )


def test_priority_result_rejects_level_that_does_not_match_score() -> None:
    with pytest.raises(ValidationError, match="expected Urgent"):
        PriorityResult(
            priority_score=0.90,
            suggested_priority="High",
            reasoning="Tutarsız seviye",
        )


def test_priority_response_uses_backend_urgent_name() -> None:
    response = PriorityScoreResponse(
        priority_score=0.90,
        suggested_priority="Urgent",
        reasoning="Acil müdahale gerekli.",
    )

    assert response.suggested_priority == "Urgent"


@pytest.mark.asyncio
async def test_priority_service_maps_provider_result(
    priority_payload: dict,
) -> None:
    provider = create_autospec(ILlmProvider, instance=True)
    provider.score_priority = AsyncMock(
        return_value=PriorityResult(
            priority_score=0.82,
            suggested_priority="Urgent",
            reasoning="Su kaçağı güvenlik riski oluşturuyor.",
        )
    )
    service = PriorityService(provider)
    request = PriorityScoreRequest.model_validate(priority_payload)

    response = await service.score_report(request)

    assert response.priority_score == 0.82
    assert response.suggested_priority == "Urgent"
    provider.score_priority.assert_awaited_once_with(
        title=request.title,
        description=request.description,
        category_name=request.category_name,
        similar_report_count=request.similar_report_count,
        days_open=request.days_open,
    )
