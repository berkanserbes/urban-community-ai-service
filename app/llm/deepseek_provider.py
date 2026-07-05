from app.core.config import settings
from .openai_provider import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    def __init__(self) -> None:
        super().__init__(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL,
            base_url=settings.DEEPSEEK_BASE_URL,
            provider_name="deepseek",
            request_options={
                "extra_body": {
                    "thinking": {
                        "type": "disabled",
                    }
                }
            },
        )
