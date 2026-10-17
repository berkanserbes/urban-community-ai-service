from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app

TEST_API_KEY = "test-ai-api-key"
FIRST_CATEGORY_ID = "018f6f64-5f47-7e37-b7dc-2f9bc8f69d42"
SECOND_CATEGORY_ID = "018f6f64-5f47-7e37-b7dc-2f9bc8f69d43"


@pytest.fixture(autouse=True)
def isolate_application_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "AI_API_KEY", TEST_API_KEY)
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-Api-Key": TEST_API_KEY}


@pytest.fixture
def categorization_payload() -> dict:
    return {
        "title": "Mahalle girişinde sokak lambası çalışmıyor",
        "description": "Üç gündür yol tamamen karanlık ve yayalar için tehlike oluşturuyor.",
        "categories": [
            {
                "id": FIRST_CATEGORY_ID,
                "name": "Aydınlatma ve Elektrik",
                "description": "Sokak lambaları ve elektrik altyapısı sorunları",
            },
            {
                "id": SECOND_CATEGORY_ID,
                "name": "Yol ve Altyapı",
                "description": "Yol yüzeyi ve altyapı sorunları",
            },
        ],
    }


@pytest.fixture
def priority_payload() -> dict:
    return {
        "title": "Ana caddede büyük su kaçağı",
        "description": "Yola yoğun miktarda su akıyor ve trafik güvenliğini etkiliyor.",
        "category_name": "Su ve Kanalizasyon",
        "similar_report_count": 3,
        "days_open": 2,
    }


@pytest.fixture
def similarity_payload() -> dict:
    return {
        "title": "Ataturk Caddesi'nde su borusu patladi",
        "description": "Marketin onunde yola yogun miktarda su akiyor.",
        "existing_reports": [
            {
                "id": FIRST_CATEGORY_ID,
                "title": "Ana caddede su sizintisi",
                "description": "Market karsisinda patlayan borudan yola su akiyor.",
                "created_at": "2026-06-08T08:00:00Z",
            },
            {
                "id": SECOND_CATEGORY_ID,
                "title": "Parkta aydinlatma arizasi",
                "description": "Mahalle parkindaki iki lamba calismiyor.",
                "created_at": "2026-06-07T18:00:00Z",
            },
        ],
    }
