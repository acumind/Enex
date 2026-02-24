"""Anthropic Claude adapter — uses tool_use for structured prediction extraction."""

import json
import logging

from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.schemas.extraction import ExtractionResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a financial analyst specializing in Indian equity markets. "
    "Your task is to extract stock price target predictions from article text. "
    "For each prediction found, call the report_predictions tool with the structured data. "
    "Only extract concrete, actionable price targets — not general market commentary. "
    "If the article contains no predictions, call report_predictions with an empty list."
)

REPORT_PREDICTIONS_TOOL = {
    "name": "report_predictions",
    "description": "Report extracted stock price predictions from the article.",
    "input_schema": {
        "type": "object",
        "properties": {
            "predictions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "predictor_name": {
                            "type": "string",
                            "description": "Full name of the analyst, firm, or media source making the prediction.",
                        },
                        "stock_name": {
                            "type": "string",
                            "description": "Company name of the stock.",
                        },
                        "stock_symbol": {
                            "type": "string",
                            "description": "NSE/BSE ticker symbol (e.g. RELIANCE, TCS, INFY).",
                        },
                        "target_price": {
                            "type": "number",
                            "description": "Predicted target price in INR.",
                        },
                        "current_price_mentioned": {
                            "type": ["number", "null"],
                            "description": "Current/reference price mentioned in article, if any.",
                        },
                        "timeframe": {
                            "type": ["string", "null"],
                            "description": "Timeframe for the prediction (e.g. '12 months', '1 year', 'short term').",
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["buy", "sell", "hold", "neutral"],
                            "description": "Recommendation direction.",
                        },
                        "raw_quote": {
                            "type": ["string", "null"],
                            "description": "Exact quote from the article containing the prediction.",
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence in extraction accuracy (0.0 to 1.0).",
                        },
                        "source_type": {
                            "type": "string",
                            "enum": [
                                "tv_interview",
                                "news_article",
                                "research_report",
                                "social_media",
                                "podcast",
                                "blog",
                                "other",
                            ],
                            "description": "Type of source material.",
                        },
                    },
                    "required": [
                        "predictor_name",
                        "stock_name",
                        "stock_symbol",
                        "target_price",
                        "direction",
                        "confidence",
                        "source_type",
                    ],
                },
            },
        },
        "required": ["predictions"],
    },
}

# Approximate: 1 token ≈ 4 chars
_CHARS_PER_TOKEN = 4


class AnthropicAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.max_input_chars = settings.ANTHROPIC_MAX_INPUT_TOKENS * _CHARS_PER_TOKEN

    async def extract_predictions(self, article_text: str) -> list[ExtractionResult]:
        truncated = article_text[: self.max_input_chars]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[REPORT_PREDICTIONS_TOOL],
                tool_choice={"type": "tool", "name": "report_predictions"},
                messages=[
                    {
                        "role": "user",
                        "content": f"Extract all stock price target predictions from this article:\n\n{truncated}",
                    }
                ],
            )
        except Exception:
            logger.exception("Anthropic API call failed")
            raise

        # Extract tool_use block
        for block in response.content:
            if block.type == "tool_use" and block.name == "report_predictions":
                raw_predictions = block.input.get("predictions", [])
                results = []
                for raw in raw_predictions:
                    try:
                        results.append(ExtractionResult.model_validate(raw))
                    except Exception:
                        logger.warning("Skipping malformed prediction: %s", json.dumps(raw)[:200])
                return results

        logger.warning("No tool_use block found in Anthropic response")
        return []
