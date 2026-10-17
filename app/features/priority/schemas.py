from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.llm.base import PriorityLevel, get_priority_for_score


class PriorityScoreRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Ana caddede büyük su kaçağı",
                "description": "Yola yoğun miktarda su akıyor ve trafik güvenliğini etkiliyor.",
                "category_name": "Su ve Kanalizasyon",
                "similar_report_count": 3,
                "days_open": 2,
            }
        },
    )

    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category_name: str = Field(..., min_length=1, max_length=100)
    similar_report_count: int = Field(default=0, ge=0, le=100)
    days_open: int = Field(default=0, ge=0, le=3650)


class PriorityScoreResponse(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "priority_score": 0.82,
                "suggested_priority": "Urgent",
                "reasoning": "Yoğun su kaçağı trafik ve altyapı güvenliği açısından acil müdahale gerektiriyor.",
            }
        },
    )

    priority_score: float = Field(ge=0.0, le=1.0)
    suggested_priority: PriorityLevel
    reasoning: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_priority_matches_score(self) -> "PriorityScoreResponse":
        expected_priority = get_priority_for_score(self.priority_score)
        if self.suggested_priority != expected_priority:
            raise ValueError(
                "suggested_priority must match the priority_score range "
                f"(expected {expected_priority})"
            )
        return self
