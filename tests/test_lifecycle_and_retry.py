from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import app


def test_settings_require_selected_provider_api_key() -> None:
    openai_settings = Settings(
        LLM_PROVIDER="openai",
        AI_API_KEY="internal-key",
        OPENAI_API_KEY="",
    )
    gemini_settings = Settings(
        LLM_PROVIDER="gemini",
        AI_API_KEY="internal-key",
        GEMINI_API_KEY="",
    )
    deepseek_settings = Settings(
        LLM_PROVIDER="deepseek",
        AI_API_KEY="internal-key",
        DEEPSEEK_API_KEY="",
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        openai_settings.validate_provider_configuration()

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        gemini_settings.validate_provider_configuration()

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        deepseek_settings.validate_provider_configuration()


def test_settings_accept_configured_provider_api_key() -> None:
    configured_settings = Settings(
        LLM_PROVIDER="openai",
        AI_API_KEY="internal-key",
        OPENAI_API_KEY="test-key",
    )

    configured_settings.validate_provider_configuration()


def test_settings_require_internal_api_key() -> None:
    configured_settings = Settings(
        LLM_PROVIDER="openai",
        AI_API_KEY="",
        OPENAI_API_KEY="test-key",
    )

    with pytest.raises(ValueError, match="AI_API_KEY"):
        configured_settings.validate_provider_configuration()


def test_provider_is_created_once_during_application_lifespan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = Mock()
    create_provider = Mock(return_value=provider)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.main.create_llm_provider", create_provider)

    with TestClient(app) as client:
        assert app.state.categorization_service.llm_provider is provider
        assert app.state.priority_service.llm_provider is provider
        assert app.state.similarity_service.llm_provider is provider

        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")
        assert live_response.status_code == 200
        assert ready_response.status_code == 200
        assert ready_response.json()["status"] == "ready"

    create_provider.assert_called_once_with()
