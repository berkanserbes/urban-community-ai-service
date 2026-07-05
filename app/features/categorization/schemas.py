from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.llm.base import CategoryItem


class CategorizationRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Mahalle girişinde sokak lambası çalışmıyor",
                "description": "Üç gündür yol tamamen karanlık ve yayalar için tehlike oluşturuyor.",
                "categories": [
                    {
                        "id": "018f6f64-5f47-7e37-b7dc-2f9bc8f69d42",
                        "name": "Aydınlatma ve Elektrik",
                        "description": "Sokak lambaları ve elektrik altyapısı sorunları",
                    }
                ],
            }
        },
    )

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    categories: list[CategoryItem] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_unique_category_ids(self) -> "CategorizationRequest":
        category_ids = [category.id for category in self.categories]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("categories must contain unique IDs")
        return self


class CategorizationResponse(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "suggested_category_id": "018f6f64-5f47-7e37-b7dc-2f9bc8f69d42",
                "suggested_category_name": "Aydınlatma ve Elektrik",
                "confidence": 0.94,
                "reasoning": "Bildirim çalışmayan sokak lambasıyla ilgilidir.",
            }
        },
    )

    suggested_category_id: UUID
    suggested_category_name: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=500)
