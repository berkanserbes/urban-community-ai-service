from app.core.exceptions import LlmInvalidResponseError
from app.llm.base import ILlmProvider, SimilarityCandidate
from .schemas import SimilarReport, SimilarityFindRequest, SimilarityFindResponse


class SimilarityService:
    def __init__(self, llm_provider: ILlmProvider) -> None:
        self.llm_provider = llm_provider

    async def find_similar_reports(
        self,
        request: SimilarityFindRequest,
    ) -> SimilarityFindResponse:
        candidate_ids = {report.id for report in request.existing_reports}
        result = await self.llm_provider.find_similar_reports(
            title=request.title,
            description=request.description,
            existing_reports=[
                SimilarityCandidate(**report.model_dump())
                for report in request.existing_reports
            ],
        )

        seen_ids = set()
        matches: list[SimilarReport] = []
        for match in result.similar_reports:
            if match.report_id not in candidate_ids or match.report_id in seen_ids:
                raise LlmInvalidResponseError(
                    "LLM benzerlik cevabi bilinmeyen veya tekrar eden rapor kimligi iceriyor"
                )
            seen_ids.add(match.report_id)
            matches.append(SimilarReport(**match.model_dump()))

        matches.sort(key=lambda match: match.similarity_score, reverse=True)
        return SimilarityFindResponse(similar_reports=matches)
