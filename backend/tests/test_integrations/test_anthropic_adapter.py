"""Tests for AnthropicAdapter: prompt structure, output parsing, edge cases."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.extraction import ExtractionResult

# ---------------------------------------------------------------------------
# Helpers to build mock Anthropic responses
# ---------------------------------------------------------------------------

def _make_tool_use_block(predictions: list[dict]) -> MagicMock:
    """Build a mock content block with type='tool_use' and name='report_predictions'."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = "report_predictions"
    block.input = {"predictions": predictions}
    return block


def _make_text_block(text: str = "Thinking...") -> MagicMock:
    """Build a mock content block with type='text' (should be ignored)."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


VALID_PREDICTION = {
    "predictor_name": "Motilal Oswal",
    "stock_name": "Reliance Industries",
    "stock_symbol": "RELIANCE",
    "target_price": 2800.0,
    "current_price_mentioned": 2500.0,
    "timeframe": "12 months",
    "direction": "buy",
    "raw_quote": "We set a target of Rs 2800 for Reliance.",
    "confidence": 0.92,
    "source_type": "research_report",
}

VALID_PREDICTION_2 = {
    "predictor_name": "HDFC Securities",
    "stock_name": "Infosys",
    "stock_symbol": "INFY",
    "target_price": 1900.0,
    "current_price_mentioned": None,
    "timeframe": None,
    "direction": "hold",
    "raw_quote": None,
    "confidence": 0.75,
    "source_type": "news_article",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@patch("app.integrations.ai.anthropic_adapter.get_settings")
@patch("app.integrations.ai.anthropic_adapter.AsyncAnthropic")
async def test_prompt_structure_and_tool_use_mode(mock_anthropic_cls: MagicMock, mock_get_settings: MagicMock) -> None:
    """Verify the adapter passes correct system prompt, tool_choice, and message structure."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-6"
    settings.ANTHROPIC_MAX_INPUT_TOKENS = 8000
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_anthropic_cls.return_value = mock_client

    # Set up the mock response with a valid tool_use block
    mock_response = MagicMock()
    mock_response.content = [_make_tool_use_block([VALID_PREDICTION])]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    from app.integrations.ai.anthropic_adapter import SYSTEM_PROMPT, AnthropicAdapter

    adapter = AnthropicAdapter()
    await adapter.extract_predictions("Some article text about stocks.")

    # Assert the API was called once with correct structure
    mock_client.messages.create.assert_awaited_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs

    assert call_kwargs["model"] == "claude-sonnet-4-6"
    assert call_kwargs["max_tokens"] == 4096
    assert call_kwargs["system"] == SYSTEM_PROMPT
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": "report_predictions"}

    # Verify tools list contains report_predictions
    tools = call_kwargs["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "report_predictions"

    # Verify user message
    messages = call_kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "Some article text about stocks." in messages[0]["content"]


@patch("app.integrations.ai.anthropic_adapter.get_settings")
@patch("app.integrations.ai.anthropic_adapter.AsyncAnthropic")
async def test_parses_valid_predictions(mock_anthropic_cls: MagicMock, mock_get_settings: MagicMock) -> None:
    """Verify that valid predictions are parsed into ExtractionResult objects."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-6"
    settings.ANTHROPIC_MAX_INPUT_TOKENS = 8000
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [_make_tool_use_block([VALID_PREDICTION, VALID_PREDICTION_2])]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    from app.integrations.ai.anthropic_adapter import AnthropicAdapter

    adapter = AnthropicAdapter()
    results = await adapter.extract_predictions("Article with two predictions.")

    assert len(results) == 2
    assert all(isinstance(r, ExtractionResult) for r in results)

    assert results[0].predictor_name == "Motilal Oswal"
    assert results[0].stock_symbol == "RELIANCE"
    assert results[0].target_price == 2800.0
    assert results[0].direction == "buy"
    assert results[0].confidence == 0.92

    assert results[1].predictor_name == "HDFC Securities"
    assert results[1].stock_symbol == "INFY"
    assert results[1].target_price == 1900.0
    assert results[1].direction == "hold"


@patch("app.integrations.ai.anthropic_adapter.get_settings")
@patch("app.integrations.ai.anthropic_adapter.AsyncAnthropic")
async def test_handles_empty_predictions(mock_anthropic_cls: MagicMock, mock_get_settings: MagicMock) -> None:
    """When the model calls report_predictions with an empty list, return []."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-6"
    settings.ANTHROPIC_MAX_INPUT_TOKENS = 8000
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [_make_tool_use_block([])]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    from app.integrations.ai.anthropic_adapter import AnthropicAdapter

    adapter = AnthropicAdapter()
    results = await adapter.extract_predictions("Article with no predictions at all.")

    assert results == []


@patch("app.integrations.ai.anthropic_adapter.get_settings")
@patch("app.integrations.ai.anthropic_adapter.AsyncAnthropic")
async def test_skips_malformed_predictions_without_crashing(
    mock_anthropic_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """Malformed predictions are skipped; valid ones in the same batch are still returned."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-6"
    settings.ANTHROPIC_MAX_INPUT_TOKENS = 8000
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_anthropic_cls.return_value = mock_client

    malformed = {
        # Missing required fields (predictor_name, stock_name, stock_symbol)
        "target_price": -100,  # Also invalid: must be > 0
        "confidence": 2.0,  # Also invalid: must be <= 1.0
    }

    mock_response = MagicMock()
    mock_response.content = [_make_tool_use_block([malformed, VALID_PREDICTION])]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    from app.integrations.ai.anthropic_adapter import AnthropicAdapter

    adapter = AnthropicAdapter()
    results = await adapter.extract_predictions("Article with one bad and one good prediction.")

    # Only the valid prediction survives
    assert len(results) == 1
    assert results[0].stock_symbol == "RELIANCE"


@patch("app.integrations.ai.anthropic_adapter.get_settings")
@patch("app.integrations.ai.anthropic_adapter.AsyncAnthropic")
async def test_returns_empty_when_no_tool_use_block(
    mock_anthropic_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """If the response contains no tool_use block, return an empty list."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-6"
    settings.ANTHROPIC_MAX_INPUT_TOKENS = 8000
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [_make_text_block("I could not find any predictions.")]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    from app.integrations.ai.anthropic_adapter import AnthropicAdapter

    adapter = AnthropicAdapter()
    results = await adapter.extract_predictions("Some random text.")

    assert results == []


@patch("app.integrations.ai.anthropic_adapter.get_settings")
@patch("app.integrations.ai.anthropic_adapter.AsyncAnthropic")
async def test_truncates_long_input(mock_anthropic_cls: MagicMock, mock_get_settings: MagicMock) -> None:
    """Input longer than max_input_chars should be truncated before sending."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-6"
    settings.ANTHROPIC_MAX_INPUT_TOKENS = 100  # 100 tokens * 4 chars = 400 chars max
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [_make_tool_use_block([])]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    from app.integrations.ai.anthropic_adapter import AnthropicAdapter

    adapter = AnthropicAdapter()
    long_text = "A" * 1000
    await adapter.extract_predictions(long_text)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    # The prefix is "Extract all stock price target predictions from this article:\n\n"
    # so the article portion should be truncated to 400 chars
    article_portion = user_content.split("\n\n", 1)[1]
    assert len(article_portion) == 400
