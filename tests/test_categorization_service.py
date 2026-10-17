from unittest.mock import AsyncMock, create_autospec

import pytest

from app.core.exceptions import LlmInvalidResponseError
from app.features.categorization.schemas import CategorizationRequest
from app.features.categorization.service import CategorizationService
from app.llm.base import CategorizationResult, ILlmProvider
from tests.conftest import FIRST_CATEGORY_ID


@pytest.mark.asyncio
async def test_service_returns_canonical_category_name(
    categorization_payload: dict,
) -> None:
    provider = create_autospec(ILlmProvider, instance=True)
    provider.categorize_report = AsyncMock(
        return_value=CategorizationResult(
            suggested_category_id=FIRST_CATEGORY_ID,
            suggested_category_name="AI tarafından değiştirilmiş isim",
            confidence=0.92,
            reasoning="Aydınlatma problemi tespit edildi.",
        )
    )
    service = CategorizationService(provider)
    request = CategorizationRequest.model_validate(categorization_payload)

    response = await service.suggest_category(request)

    assert response.suggested_category_name == "Aydınlatma ve Elektrik"
    assert response.confidence == 0.92
    provider.categorize_report.assert_awaited_once_with(
        title=request.title,
        description=request.description,
        categories=request.categories,
    )


@pytest.mark.asyncio
async def test_service_rejects_category_not_supplied_in_request(
    categorization_payload: dict,
) -> None:
    provider = create_autospec(ILlmProvider, instance=True)
    provider.categorize_report = AsyncMock(
        return_value=CategorizationResult(
            suggested_category_id="018f6f64-5f47-7e37-b7dc-2f9bc8f69d99",
            suggested_category_name="Bilinmeyen kategori",
            confidence=0.95,
            reasoning="Geçersiz kategori seçimi",
        )
    )
    service = CategorizationService(provider)
    request = CategorizationRequest.model_validate(categorization_payload)

    with pytest.raises(LlmInvalidResponseError):
        await service.suggest_category(request)
