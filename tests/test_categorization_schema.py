from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.features.categorization.schemas import (
    CategorizationRequest,
    CategorizationResponse,
)
from app.llm.base import CategorizationResult
from tests.conftest import FIRST_CATEGORY_ID


def test_valid_categorization_request_is_normalized(
    categorization_payload: dict,
) -> None:
    categorization_payload["title"] = "  Geçerli başlık  "

    request = CategorizationRequest.model_validate(categorization_payload)

    assert request.title == "Geçerli başlık"
    assert str(request.categories[0].id) == FIRST_CATEGORY_ID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "ab"),
        ("title", "a" * 201),
        ("description", "kısa"),
        ("description", "a" * 2001),
    ],
)
def test_categorization_request_rejects_invalid_text_lengths(
    categorization_payload: dict,
    field: str,
    value: str,
) -> None:
    payload = deepcopy(categorization_payload)
    payload[field] = value

    with pytest.raises(ValidationError):
        CategorizationRequest.model_validate(payload)


def test_categorization_request_requires_at_least_one_category(
    categorization_payload: dict,
) -> None:
    categorization_payload["categories"] = []

    with pytest.raises(ValidationError):
        CategorizationRequest.model_validate(categorization_payload)


def test_categorization_request_rejects_more_than_fifty_categories(
    categorization_payload: dict,
) -> None:
    base_category = categorization_payload["categories"][0]
    categorization_payload["categories"] = [
        {
            **base_category,
            "id": f"00000000-0000-0000-0000-{index:012d}",
        }
        for index in range(1, 52)
    ]

    with pytest.raises(ValidationError):
        CategorizationRequest.model_validate(categorization_payload)


def test_categorization_request_rejects_invalid_category_uuid(
    categorization_payload: dict,
) -> None:
    categorization_payload["categories"][0]["id"] = "not-a-uuid"

    with pytest.raises(ValidationError):
        CategorizationRequest.model_validate(categorization_payload)


def test_categorization_request_rejects_duplicate_category_ids(
    categorization_payload: dict,
) -> None:
    categorization_payload["categories"][1]["id"] = FIRST_CATEGORY_ID

    with pytest.raises(ValidationError, match="unique IDs"):
        CategorizationRequest.model_validate(categorization_payload)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_categorization_result_rejects_invalid_confidence(
    confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        CategorizationResult(
            suggested_category_id=FIRST_CATEGORY_ID,
            suggested_category_name="Aydınlatma ve Elektrik",
            confidence=confidence,
            reasoning="Geçerli açıklama",
        )


def test_categorization_response_serializes_uuid_as_string() -> None:
    response = CategorizationResponse(
        suggested_category_id=FIRST_CATEGORY_ID,
        suggested_category_name="Aydınlatma ve Elektrik",
        confidence=0.91,
        reasoning="Geçerli açıklama",
    )

    assert response.model_dump(mode="json")["suggested_category_id"] == FIRST_CATEGORY_ID
