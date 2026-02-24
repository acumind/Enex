"""Extraction service — orchestrates content fetching and AI extraction."""

from app.integrations.ai.anthropic_adapter import AnthropicAdapter
from app.integrations.content_fetcher import ContentFetcher
from app.schemas.extraction import ExtractionResponse


class ExtractionService:
    def __init__(self) -> None:
        self.fetcher = ContentFetcher()
        self.adapter = AnthropicAdapter()

    async def extract_from_url(self, url: str) -> ExtractionResponse:
        article_text, content_length = await self.fetcher.fetch(url)
        predictions = await self.adapter.extract_predictions(article_text)
        return ExtractionResponse(
            url=url,
            predictions=predictions,
            source_text_length=content_length,
        )
