"""Tests for ContentFetcher: HTML extraction, content length, and cap at 32000 chars."""

from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_response(html: str, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response with .text and .raise_for_status()."""
    response = MagicMock()
    response.text = html
    response.status_code = status_code
    response.raise_for_status = MagicMock()
    return response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@patch("app.integrations.content_fetcher.httpx.AsyncClient")
async def test_extracts_text_from_html(mock_async_client_cls: MagicMock) -> None:
    """Plain text is extracted from HTML; scripts, styles, nav, footer, header, aside are removed."""
    html = """
    <html>
    <head><title>Test Article</title></head>
    <body>
        <header><nav>Site navigation</nav></header>
        <script>var x = 1;</script>
        <style>.body { color: red; }</style>
        <article>
            <h1>Stock Prediction</h1>
            <p>Analyst says buy RELIANCE at Rs 2800.</p>
        </article>
        <aside>Related articles</aside>
        <footer>Copyright 2026</footer>
    </body>
    </html>
    """
    mock_response = _make_mock_response(html)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.content_fetcher import ContentFetcher

    fetcher = ContentFetcher()
    text, original_length = await fetcher.fetch("https://example.com/article")

    # The extracted text should contain article content
    assert "Stock Prediction" in text
    assert "Analyst says buy RELIANCE at Rs 2800." in text

    # Script, style, nav, footer, header, aside content should be removed
    assert "var x = 1" not in text
    assert ".body { color: red; }" not in text
    assert "Site navigation" not in text
    assert "Copyright 2026" not in text
    assert "Related articles" not in text


@patch("app.integrations.content_fetcher.httpx.AsyncClient")
async def test_returns_content_length(mock_async_client_cls: MagicMock) -> None:
    """The second return value should be the original text length (before any truncation)."""
    html = "<html><body><p>Short article content.</p></body></html>"
    mock_response = _make_mock_response(html)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.content_fetcher import ContentFetcher

    fetcher = ContentFetcher()
    text, original_length = await fetcher.fetch("https://example.com/short")

    assert "Short article content." in text
    assert original_length == len(text)
    assert original_length > 0


@patch("app.integrations.content_fetcher.httpx.AsyncClient")
async def test_caps_content_at_32000_chars(mock_async_client_cls: MagicMock) -> None:
    """Content longer than 32000 characters should be truncated, but original_length is preserved."""
    # Create a paragraph that repeats enough to exceed 32000 chars
    paragraph = "A" * 1000
    # 50 paragraphs = 50000 chars of raw text (well over 32000)
    body_content = "".join(f"<p>{paragraph}</p>" for _ in range(50))
    html = f"<html><body>{body_content}</body></html>"

    mock_response = _make_mock_response(html)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.content_fetcher import ContentFetcher

    fetcher = ContentFetcher()
    text, original_length = await fetcher.fetch("https://example.com/long-article")

    # Text should be capped at 32000
    assert len(text) == 32000
    # Original length should reflect the un-truncated size
    assert original_length > 32000


@patch("app.integrations.content_fetcher.httpx.AsyncClient")
async def test_strips_tags_completely(mock_async_client_cls: MagicMock) -> None:
    """HTML tags themselves should not appear in the extracted text."""
    html = """
    <html><body>
        <div class="content">
            <span style="font-weight:bold">Bold text</span>
            <a href="https://example.com">Link text</a>
            <img src="photo.jpg" alt="Photo" />
        </div>
    </body></html>
    """
    mock_response = _make_mock_response(html)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.content_fetcher import ContentFetcher

    fetcher = ContentFetcher()
    text, _ = await fetcher.fetch("https://example.com/tags")

    assert "Bold text" in text
    assert "Link text" in text
    # No raw HTML tags in output
    assert "<div" not in text
    assert "<span" not in text
    assert "<a " not in text
    assert "<img" not in text


@patch("app.integrations.content_fetcher.httpx.AsyncClient")
async def test_passes_user_agent_header(mock_async_client_cls: MagicMock) -> None:
    """The fetcher should send requests with a browser-like User-Agent header."""
    html = "<html><body><p>Content</p></body></html>"
    mock_response = _make_mock_response(html)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.content_fetcher import _USER_AGENT, ContentFetcher

    fetcher = ContentFetcher()
    await fetcher.fetch("https://example.com/ua-test")

    mock_client.get.assert_awaited_once()
    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["headers"]["User-Agent"] == _USER_AGENT
