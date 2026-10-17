from fastapi import APIRouter, Depends, Request

from app.core.security import verify_api_key
from .schemas import SimilarityFindRequest, SimilarityFindResponse
from .service import SimilarityService

router = APIRouter(
    prefix="/similarity",
    tags=["Similarity"],
    dependencies=[Depends(verify_api_key)],
)


def get_service(request: Request) -> SimilarityService:
    return request.app.state.similarity_service


@router.post("/find", response_model=SimilarityFindResponse)
async def find_similar_reports(
    request: SimilarityFindRequest,
    service: SimilarityService = Depends(get_service),
) -> SimilarityFindResponse:
    return await service.find_similar_reports(request)
