import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from .exceptions import (
    LlmAuthenticationError,
    LlmInvalidResponseError,
    LlmProviderError,
    LlmRateLimitError,
)

logger = logging.getLogger(__name__)


async def llm_rate_limit_handler(request: Request, exc: LlmRateLimitError) -> JSONResponse:
    logger.warning("LLM rate limit aşıldı: %s", exc)
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "message": "LLM servisinin istek limiti aşıldı. Lütfen bekleyin."},
    )


async def llm_authentication_handler(request: Request, exc: LlmAuthenticationError) -> JSONResponse:
    logger.error("LLM kimlik doğrulama hatası: %s", exc)
    return JSONResponse(
        status_code=424,
        content={"error": "llm_authentication_error", "message": "LLM servisine bağlanılamadı: geçersiz API anahtarı."},
    )


async def llm_invalid_response_handler(request: Request, exc: LlmInvalidResponseError) -> JSONResponse:
    logger.error("LLM geçersiz yanıt döndürdü: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"error": "llm_invalid_response", "message": "LLM servisi geçerli bir yanıt döndüremedi."},
    )


async def llm_provider_handler(request: Request, exc: LlmProviderError) -> JSONResponse:
    logger.error("LLM provider hatası: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "llm_provider_error", "message": "LLM servisinde beklenmeyen bir hata oluştu."},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Beklenmeyen hata: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "Beklenmeyen bir hata oluştu."},
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(LlmRateLimitError, llm_rate_limit_handler)
    app.add_exception_handler(LlmAuthenticationError, llm_authentication_handler)
    app.add_exception_handler(LlmInvalidResponseError, llm_invalid_response_handler)
    app.add_exception_handler(LlmProviderError, llm_provider_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
