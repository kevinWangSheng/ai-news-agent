import httpx
import pytest

from app.ingestion.sources.web import WebSource, build_web_sources


LISTING_HTML = """
<html><body>
  <a href="/news/model-context-protocol">MCP</a>
  <a href="https://www.anthropic.com/news/claude-update?utm=1#x">Claude</a>
  <a href="/research/not-news">Research</a>
  <a href="https://example.com/news/external">External</a>
  <a href="/news/model-context-protocol">Duplicate</a>
  <a href="mailto:hello@example.com">Mail</a>
</body></html>
"""

ARTICLE_HTML = """
<html>
<head>
  <meta property="og:title" content="Claude ships useful agents">
  <meta property="article:published_time" content="2026-05-17T12:00:00Z">
  <meta name="author" content="Anthropic">
</head>
<body>
  <article>
    <h1>Claude ships useful agents</h1>
    <p>Claude now supports a richer agent workflow with tool use, memory, and safer browser automation.</p>
    <p>This paragraph is intentionally long enough for trafilatura to extract meaningful markdown content in tests.</p>
    <p>Teams can use it to coordinate research, coding, review, and publication workflows with clearer handoffs.</p>
  </article>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_extract_article_urls_filters_same_host_pattern_and_dedupes():
    src = WebSource(
        name="Anthropic News",
        listing_url="https://www.anthropic.com/news",
        link_pattern=r"^/news/[a-z0-9-]+$",
    )

    urls = src._extract_article_urls(LISTING_HTML)

    assert urls == [
        "https://www.anthropic.com/news/model-context-protocol",
        "https://www.anthropic.com/news/claude-update",
    ]


@pytest.mark.asyncio
async def test_fetch_article_extracts_markdown_metadata(monkeypatch):
    transport = httpx.MockTransport(lambda req: httpx.Response(200, text=ARTICLE_HTML))
    real_init = httpx.AsyncClient.__init__

    def fake_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        return real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", fake_init)
    src = WebSource(
        name="Anthropic News",
        listing_url="https://www.anthropic.com/news",
        article_min_chars=40,
    )

    item = await src._fetch_article("https://www.anthropic.com/news/claude-agents")

    assert item is not None
    assert item.source_type == "web"
    assert item.source_name == "Anthropic News"
    assert item.title == "Claude ships useful agents"
    assert item.author == "Anthropic"
    assert item.published_at is not None
    assert "richer agent workflow" in item.content_md


@pytest.mark.asyncio
async def test_fetch_listing_to_items_happy_path(monkeypatch):
    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url) == "https://www.anthropic.com/news":
            return httpx.Response(200, text='<a href="/news/claude-agents">Claude agents</a>')
        return httpx.Response(200, text=ARTICLE_HTML)

    transport = httpx.MockTransport(handler)
    real_init = httpx.AsyncClient.__init__

    def fake_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        return real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", fake_init)
    src = WebSource(
        name="Anthropic News",
        listing_url="https://www.anthropic.com/news",
        link_pattern=r"^/news/[a-z0-9-]+$",
        max_items=5,
        article_min_chars=40,
    )

    items = await src.fetch()

    assert len(items) == 1
    assert items[0].url == "https://www.anthropic.com/news/claude-agents"
    assert items[0].source_meta["content_source"] == "web_http_trafilatura"


@pytest.mark.asyncio
async def test_fetch_uses_fallback_listing_when_primary_has_no_links(monkeypatch):
    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url) == "https://qwen.ai/blog":
            return httpx.Response(200, text="<html><body>No links here</body></html>")
        if str(req.url) == "https://qwenlm.github.io/blog/":
            return httpx.Response(200, text='<a href="/blog/qwen3guard/">Qwen3Guard</a>')
        return httpx.Response(200, text=ARTICLE_HTML)

    transport = httpx.MockTransport(handler)
    real_init = httpx.AsyncClient.__init__

    def fake_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        return real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", fake_init)
    src = WebSource(
        name="Qwen Blog",
        listing_url="https://qwen.ai/blog",
        fallback_urls=["https://qwenlm.github.io/blog/"],
        link_pattern=r"^/blog/[a-z0-9-]+/?$",
        article_min_chars=40,
    )

    items = await src.fetch()

    assert len(items) == 1
    assert items[0].url == "https://qwenlm.github.io/blog/qwen3guard"
    assert items[0].source_meta["listing_url"] == "https://qwenlm.github.io/blog/"


def test_build_web_sources_filters_type_and_disabled():
    cfg = {
        "tech_sources": {
            "official_blogs": [
                {"name": "RSS", "url": "https://example.com/feed", "type": "rss"},
                {
                    "name": "Web",
                    "url": "https://example.com/blog",
                    "type": "web",
                    "fallback_urls": ["https://backup.example/blog"],
                },
                {"name": "Dead", "url": "https://dead.example", "type": "web", "disabled": True},
            ]
        }
    }

    sources = build_web_sources(cfg)

    assert [s.name for s in sources] == ["Web"]
    assert sources[0].fallback_urls == ["https://backup.example/blog"]
