"""Extraction request/response schemas for AI-assisted prediction extraction."""

from pydantic import BaseModel, Field, field_validator


class ExtractionResult(BaseModel):
    predictor_name: str
    stock_name: str
    stock_symbol: str
    target_price: float = Field(..., gt=0)
    current_price_mentioned: float | None = None
    timeframe: str | None = None
    direction: str = "buy"
    raw_quote: str | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_type: str = "news_article"


class ExtractionRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ExtractionResponse(BaseModel):
    url: str
    predictions: list[ExtractionResult]
    source_text_length: int
