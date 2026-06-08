from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_PROVIDER: Literal["openai", "gemini", "deepseek"] = "openai"

    AI_API_KEY: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Provider reliability
    LLM_REQUEST_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0, le=120)
    LLM_MAX_OUTPUT_TOKENS: int = Field(default=500, ge=100, le=4000)
    LLM_MAX_RETRIES: int = Field(default=2, ge=0, le=5)
    LLM_RETRY_BASE_DELAY_SECONDS: float = Field(default=0.5, ge=0.1, le=10)

    model_config = {"env_file": ".env", "extra": "ignore"}

    def validate_provider_configuration(self) -> None:
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY.strip():
            raise ValueError("OPENAI_API_KEY must be configured when LLM_PROVIDER=openai")
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY.strip():
            raise ValueError("GEMINI_API_KEY must be configured when LLM_PROVIDER=gemini")
        if self.LLM_PROVIDER == "deepseek" and not self.DEEPSEEK_API_KEY.strip():
            raise ValueError("DEEPSEEK_API_KEY must be configured when LLM_PROVIDER=deepseek")


settings = Settings()
