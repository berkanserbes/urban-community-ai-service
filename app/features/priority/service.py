from app.llm.base import ILlmProvider
from .schemas import PriorityScoreRequest, PriorityScoreResponse


class PriorityService:
    def __init__(self, llm_provider: ILlmProvider) -> None:
        self.llm_provider = llm_provider

    async def score_report(self, request: PriorityScoreRequest) -> PriorityScoreResponse:
        result = await self.llm_provider.score_priority(
            title=request.title,
            description=request.description,
            category_name=request.category_name,
            similar_report_count=request.similar_report_count,
            days_open=request.days_open,
        )
        return PriorityScoreResponse(**result.model_dump())
