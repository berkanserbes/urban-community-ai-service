from unittest.mock import Mock

import pytest

from app.core.config import settings
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.factory import create_llm_provider


def test_factory_creates_deepseek_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "deepseek")
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "test-key")

    provider = create_llm_provider()

    assert isinstance(provider, DeepSeekProvider)
    assert provider.provider_name == "deepseek"
    assert provider.model == "deepseek-v4-flash"
    assert provider.request_options == {
        "extra_body": {"thinking": {"type": "disabled"}}
    }


def test_deepseek_provider_uses_configured_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client_factory = Mock()
    monkeypatch.setattr(
        "app.llm.openai_provider.AsyncOpenAI",
        client_factory,
    )
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "secret-key")
    monkeypatch.setattr(
        settings,
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    )

    DeepSeekProvider()

    client_factory.assert_called_once_with(
        api_key="secret-key",
        base_url="https://api.deepseek.com",
        timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )
