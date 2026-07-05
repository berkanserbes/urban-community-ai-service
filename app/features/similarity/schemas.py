from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExistingReport(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    created_at: datetime


class SimilarityFindRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    existing_reports: list[ExistingReport] = Field(min_length=1, max_length=20)


class SimilarReport(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    report_id: UUID
    similarity_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=500)


class SimilarityFindResponse(BaseModel):
    similar_reports: list[SimilarReport] = Field(max_length=10)
