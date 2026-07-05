from app.core.exceptions import LlmInvalidResponseError
from app.llm.base import ILlmProvider
from .schemas import CategorizationRequest, CategorizationResponse


class CategorizationService:
    def __init__(self, llm_provider: ILlmProvider) -> None:
        self.llm_provider = llm_provider

    async def suggest_category(self, request: CategorizationRequest) -> CategorizationResponse:
        result = await self.llm_provider.categorize_report(
            title=request.title,
            description=request.description,
            categories=request.categories,
        )

        matched_category = next(
            (
                category
                for category in request.categories
                if category.id == result.suggested_category_id
            ),
            None,
        )

        if matched_category is None:
            raise LlmInvalidResponseError(
                "LLM, istekte bulunmayan bir kategori kimliği döndürdü."
            )

        return CategorizationResponse(
            suggested_category_id=matched_category.id,
            suggested_category_name=matched_category.name,
            confidence=result.confidence,
            reasoning=result.reasoning,
        )
