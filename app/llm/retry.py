import asyncio
import random

from app.core.config import settings


async def wait_before_retry(attempt: int) -> None:
    base_delay = settings.LLM_RETRY_BASE_DELAY_SECONDS * (2**attempt)
    jitter = random.uniform(0, base_delay * 0.25)
    await asyncio.sleep(base_delay + jitter)
