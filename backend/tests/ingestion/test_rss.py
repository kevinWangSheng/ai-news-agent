import httpx
import pytest

from app.ingestion.sources.rss import RssSource


FAKE_RSS = b"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"><channel>
<title>fake</title>
<item>
  <title>Hello MCP</title>
  <link>https://example.com/posts/1</link>
  <author>alice</author>
  <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
  <description>summary</description>
</item>
</channel></rss>
"""


@pytest.mark.asyncio
async def test_rss_parses_entries(monkeypatch):
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=FAKE_RSS))
    real_init = httpx.AsyncClient.__init__

    def fake_init(self, *a, **kw):
        kw["transport"] = transport
        return real_init(self, *a, **kw)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", fake_init)
    src = RssSource(name="fake", urls=["https://example.com/feed"], max_items=10)
    items = await src.fetch()
    assert len(items) == 1
    assert items[0].title == "Hello MCP"
    assert items[0].url == "https://example.com/posts/1"
    assert items[0].source_type == "rss"
    assert items[0].source_name == "fake"


def test_build_rss_sources_filters_non_rss_and_disabled():
    from app.ingestion.sources.rss import build_rss_sources

    cfg = {
        "tech_sources": {
            "official_blogs": [
                {"name": "RSS", "url": "https://example.com/feed", "type": "rss"},
                {"name": "Web", "url": "https://example.com/blog", "type": "web"},
                {"name": "Off", "url": "https://example.com/off.xml", "type": "rss", "disabled": True},
            ]
        }
    }

    sources = build_rss_sources(cfg)

    assert [s.name for s in sources] == ["RSS"]
