"""AI extraction protocol — interface for swappable AI providers."""

from typing import Protocol, runtime_checkable

from app.schemas.extraction import ExtractionResult


@runtime_checkable
class AIExtractionProtocol(Protocol):
    async def extract_predictions(self, article_text: str) -> list[ExtractionResult]: ...
