class AiServiceError(Exception):
    """Tüm AI servis hatalarının base class'ı."""
    pass


class LlmProviderError(AiServiceError):
    """LLM API çağrısı başarısız olduğunda fırlatılır."""
    pass


class LlmRateLimitError(LlmProviderError):
    """LLM API rate limit aşıldığında fırlatılır."""
    pass


class LlmAuthenticationError(LlmProviderError):
    """Geçersiz API key gibi kimlik doğrulama hatalarında fırlatılır."""
    pass


class LlmInvalidResponseError(LlmProviderError):
    """LLM geçersiz veya parse edilemeyen bir yanıt döndürdüğünde fırlatılır."""
    pass
