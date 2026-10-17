from fastapi import APIRouter, Depends, Request

from app.core.security import verify_api_key
from .schemas import PriorityScoreRequest, PriorityScoreResponse
from .service import PriorityService

router = APIRouter(
    prefix="/priority",
    tags=["Priority"],
    dependencies=[Depends(verify_api_key)],
)


def get_service(request: Request) -> PriorityService:
    return request.app.state.priority_service


@router.post("/score", response_model=PriorityScoreResponse)
async def score_priority(
    request: PriorityScoreRequest,
    service: PriorityService = Depends(get_service),
) -> PriorityScoreResponse:
    """Rapor öncelik skoru döndürür (0.0 - 1.0) ve Low/Medium/High/Urgent seviyesi önerir."""
    return await service.score_report(request)
