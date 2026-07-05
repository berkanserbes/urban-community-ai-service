import functools
import logging
import time
from contextvars import ContextVar
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")

_token_usage: ContextVar[dict[str, int] | None] = ContextVar(
    "llm_token_usage",
    default=None,
)


def set_token_usage(
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
) -> None:
    _token_usage.set(
        {
            "input_tokens": input_tokens or 0,
            "output_tokens": output_tokens or 0,
            "total_tokens": total_tokens or 0,
        }
    )


def observe_llm_call(
    provider_name: str | None,
    operation: str,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    def decorator(
        function: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[T]]:
        @functools.wraps(function)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            logger = logging.getLogger(self.__class__.__module__)
            usage_token = _token_usage.set(None)
            started_at = time.perf_counter()
            outcome = "success"

            try:
                return await function(self, *args, **kwargs)
            except Exception:
                outcome = "failure"
                raise
            finally:
                duration_ms = round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                )
                usage = _token_usage.get() or {}
                logger.info(
                    "LLM call completed.",
                    extra={
                        "event": "llm_call_completed",
                        "provider": provider_name or self.provider_name,
                        "model": self.model,
                        "operation": operation,
                        "outcome": outcome,
                        "duration_ms": duration_ms,
                        **usage,
                    },
                )
                _token_usage.reset(usage_token)

        return wrapper

    return decorator
