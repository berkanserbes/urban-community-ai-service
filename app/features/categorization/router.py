from fastapi import APIRouter, Depends, Request

from app.core.security import verify_api_key
from .schemas import CategorizationRequest, CategorizationResponse
from .service import CategorizationService

router = APIRouter(
    prefix="/categorization",
    tags=["Categorization"],
    dependencies=[Depends(verify_api_key)],
)


def get_service(request: Request) -> CategorizationService:
    return request.app.state.categorization_service


@router.post("/suggest", response_model=CategorizationResponse)
async def suggest_category(
    request: CategorizationRequest,
    service: CategorizationService = Depends(get_service),
) -> CategorizationResponse:
    return await service.suggest_category(request)
