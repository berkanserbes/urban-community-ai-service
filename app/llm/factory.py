from app.core.config import settings
from .base import ILlmProvider


def create_llm_provider() -> ILlmProvider:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider()

    if provider == "deepseek":
        from .deepseek_provider import DeepSeekProvider
        return DeepSeekProvider()

    from .openai_provider import OpenAIProvider
    return OpenAIProvider()
