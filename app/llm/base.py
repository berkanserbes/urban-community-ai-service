from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

PriorityLevel = Literal["Low", "Medium", "High", "Urgent"]

class CategoryItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategorizationResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    suggested_category_id: UUID
    suggested_category_name: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=500)


class PriorityResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    priority_score: float = Field(ge=0.0, le=1.0)
    suggested_priority: PriorityLevel
    reasoning: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_priority_matches_score(self) -> "PriorityResult":
        expected_priority = get_priority_for_score(self.priority_score)
        if self.suggested_priority != expected_priority:
            raise ValueError(
                "suggested_priority must match the priority_score range "
                f"(expected {expected_priority})"
            )
        return self


class SimilarityCandidate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    created_at: datetime


class SimilarityMatch(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    report_id: UUID
    similarity_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=500)


class SimilarityResult(BaseModel):
    similar_reports: list[SimilarityMatch] = Field(max_length=10)


def get_priority_for_score(score: float) -> PriorityLevel:
    if score <= 0.25:
        return "Low"
    if score <= 0.50:
        return "Medium"
    if score <= 0.75:
        return "High"
    return "Urgent"


class ILlmProvider(ABC):
    @abstractmethod
    async def categorize_report(
        self,
        title: str,
        description: str,
        categories: list[CategoryItem],
    ) -> CategorizationResult:
        pass

    @abstractmethod
    async def score_priority(
        self,
        title: str,
        description: str,
        category_name: str,
        similar_report_count: int,
        days_open: int,
    ) -> PriorityResult:
        pass

    @abstractmethod
    async def find_similar_reports(
        self,
        title: str,
        description: str,
        existing_reports: list[SimilarityCandidate],
    ) -> SimilarityResult:
        pass
