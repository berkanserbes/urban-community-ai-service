from dataclasses import dataclass

import pytest
from httpx import AsyncClient

from app.core.exceptions import LlmInvalidResponseError, LlmRateLimitError
from app.features.categorization.router import get_service as get_categorization_service
from app.features.categorization.schemas import (
    CategorizationRequest,
    CategorizationResponse,
)
from app.features.priority.router import get_service as get_priority_service
from app.features.priority.schemas import PriorityScoreRequest, PriorityScoreResponse
from app.features.similarity.router import get_service as get_similarity_service
from app.features.similarity.schemas import SimilarityFindRequest, SimilarityFindResponse
from app.main import app
from tests.conftest import FIRST_CATEGORY_ID


@dataclass
class StubCategorizationService:
    response: CategorizationResponse | None = None
    error: Exception | None = None

    async def suggest_category(
        self,
        request: CategorizationRequest,
    ) -> CategorizationResponse:
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


@dataclass
class StubPriorityService:
    response: PriorityScoreResponse

    async def score_report(
        self,
        request: PriorityScoreRequest,
    ) -> PriorityScoreResponse:
        return self.response


@dataclass
class StubSimilarityService:
    response: SimilarityFindResponse

    async def find_similar_reports(
        self,
        request: SimilarityFindRequest,
    ) -> SimilarityFindResponse:
        return self.response


def override_categorization_service(service: StubCategorizationService) -> None:
    app.dependency_overrides[get_categorization_service] = lambda: service


def override_priority_service(service: StubPriorityService) -> None:
    app.dependency_overrides[get_priority_service] = lambda: service


def override_similarity_service(service: StubSimilarityService) -> None:
    app.dependency_overrides[get_similarity_service] = lambda: service


def successful_categorization_service() -> StubCategorizationService:
    return StubCategorizationService(
        response=CategorizationResponse(
            suggested_category_id=FIRST_CATEGORY_ID,
            suggested_category_name="Aydınlatma ve Elektrik",
            confidence=0.94,
            reasoning="Aydınlatma problemi tespit edildi.",
        )
    )


@pytest.mark.asyncio
async def test_api_rejects_missing_api_key(
    client: AsyncClient,
    categorization_payload: dict,
) -> None:
    override_categorization_service(successful_categorization_service())

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Geçersiz veya eksik API anahtarı."


@pytest.mark.asyncio
async def test_api_preserves_supplied_correlation_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    categorization_payload: dict,
) -> None:
    override_categorization_service(successful_categorization_service())
    headers = {
        **auth_headers,
        "X-Correlation-ID": "report-ai-review-123",
    }

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "report-ai-review-123"


@pytest.mark.asyncio
async def test_api_generates_correlation_id_when_missing(
    client: AsyncClient,
) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"]


@pytest.mark.asyncio
async def test_api_rejects_invalid_api_key(
    client: AsyncClient,
    categorization_payload: dict,
) -> None:
    override_categorization_service(successful_categorization_service())

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
        headers={"X-Api-Key": "wrong-key"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_categorization_endpoint_returns_valid_response(
    client: AsyncClient,
    auth_headers: dict[str, str],
    categorization_payload: dict,
) -> None:
    override_categorization_service(successful_categorization_service())

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "suggested_category_id": FIRST_CATEGORY_ID,
        "suggested_category_name": "Aydınlatma ve Elektrik",
        "confidence": 0.94,
        "reasoning": "Aydınlatma problemi tespit edildi.",
    }


@pytest.mark.asyncio
async def test_categorization_endpoint_returns_422_for_invalid_request(
    client: AsyncClient,
    auth_headers: dict[str, str],
    categorization_payload: dict,
) -> None:
    override_categorization_service(successful_categorization_service())
    categorization_payload["categories"] = []

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_priority_endpoint_returns_valid_response(
    client: AsyncClient,
    auth_headers: dict[str, str],
    priority_payload: dict,
) -> None:
    override_priority_service(
        StubPriorityService(
            response=PriorityScoreResponse(
                priority_score=0.82,
                suggested_priority="Urgent",
                reasoning="Acil müdahale gerekli.",
            )
        )
    )

    response = await client.post(
        "/api/priority/score",
        json=priority_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["suggested_priority"] == "Urgent"
    assert response.json()["priority_score"] == 0.82


@pytest.mark.asyncio
async def test_similarity_endpoint_returns_valid_response(
    client: AsyncClient,
    auth_headers: dict[str, str],
    similarity_payload: dict,
) -> None:
    override_similarity_service(
        StubSimilarityService(
            response=SimilarityFindResponse(similar_reports=[])
        )
    )

    response = await client.post(
        "/api/similarity/find",
        json=similarity_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"similar_reports": []}


@pytest.mark.asyncio
async def test_rate_limit_exception_handler_returns_429(
    client: AsyncClient,
    auth_headers: dict[str, str],
    categorization_payload: dict,
) -> None:
    override_categorization_service(
        StubCategorizationService(error=LlmRateLimitError("rate limited"))
    )

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
        headers=auth_headers,
    )

    assert response.status_code == 429
    assert response.json()["error"] == "rate_limit_exceeded"


@pytest.mark.asyncio
async def test_invalid_llm_response_handler_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    categorization_payload: dict,
) -> None:
    override_categorization_service(
        StubCategorizationService(
            error=LlmInvalidResponseError("invalid provider response")
        )
    )

    response = await client.post(
        "/api/categorization/suggest",
        json=categorization_payload,
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "llm_invalid_response"
