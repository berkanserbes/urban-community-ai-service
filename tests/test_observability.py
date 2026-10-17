import logging

import pytest

from app.llm.observability import observe_llm_call, set_token_usage


class ObservableProvider:
    model = "test-model"

    @observe_llm_call("test-provider", "test-operation")
    async def execute(self) -> str:
        set_token_usage(10, 4, 14)
        return "sensitive-result"


@pytest.mark.asyncio
async def test_llm_observability_logs_metadata_without_result_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    provider = ObservableProvider()

    with caplog.at_level(logging.INFO):
        result = await provider.execute()

    assert result == "sensitive-result"
    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", None) == "llm_call_completed"
    )
    assert record.provider == "test-provider"
    assert record.model == "test-model"
    assert record.operation == "test-operation"
    assert record.outcome == "success"
    assert record.input_tokens == 10
    assert record.output_tokens == 4
    assert record.total_tokens == 14
    assert "sensitive-result" not in record.getMessage()
