from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.features.categorization.router import router as categorization_router
from app.features.categorization.service import CategorizationService
from app.features.priority.router import router as priority_router
from app.features.priority.service import PriorityService
from app.features.similarity.router import router as similarity_router
from app.features.similarity.service import SimilarityService
from app.llm.factory import create_llm_provider

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_provider_configuration()
    provider = create_llm_provider()
    app.state.categorization_service = CategorizationService(provider)
    app.state.priority_service = PriorityService(provider)
    app.state.similarity_service = SimilarityService(provider)
    yield


app = FastAPI(
    title="Urban Community AI Service",
    description="AI-powered services for Urban Community platform",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)

app.include_router(categorization_router, prefix="/api")
app.include_router(priority_router, prefix="/api")
app.include_router(similarity_router, prefix="/api")


@app.get("/health/live", tags=["Health"])
def liveness_check() -> dict:
    return {"status": "healthy"}


@app.get("/health/ready", tags=["Health"])
def readiness_check() -> JSONResponse:
    services_ready = all(
        hasattr(app.state, service_name)
        for service_name in (
            "categorization_service",
            "priority_service",
            "similarity_service",
        )
    )
    return JSONResponse(
        status_code=200 if services_ready else 503,
        content={
            "status": "ready" if services_ready else "not_ready",
            "provider": settings.LLM_PROVIDER,
        },
    )


@app.get("/health", include_in_schema=False)
def health_check() -> dict:
    return liveness_check()
