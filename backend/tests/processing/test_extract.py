"""Unit-level extract test using static HTML via MockTransport."""
from types import SimpleNamespace

import httpx
import pytest

from app.processing.extract import extract_one
from app.processing.extract import _extract_html_text


HTML = """<html><body><article>
<h1>An article about MCP</h1>
<p>Model Context Protocol is a protocol for LLM tools.</p>
</article></body></html>"""

EMAIL_BODY_HTML = """<html><body>
<nav>Archive Subscribe Search</nav>
<article class="email-body">
<h1>Newsletter title</h1>
<p>This is a long newsletter body about agents, model routing, browser automation,
and AI engineering practice.</p>
<p>It contains enough text for a structured fallback to beat a failed readability
extractor and should preserve the core article content.</p>
</article>
</body></html>"""


class FakeSession:
    def add(self, *a, **kw):
        pass

    async def commit(self):
        pass

    async def flush(self):
        pass


@pytest.mark.asyncio
async def test_extract_uses_trafilatura(monkeypatch):
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=HTML))
    real_init = httpx.AsyncClient.__init__

    def fake_init(self, *a, **kw):
        kw["transport"] = transport
        return real_init(self, *a, **kw)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", fake_init)

    item = SimpleNamespace(
        url="https://example.com/post",
        source_type="rss",
        content_md=None,
        processing_status="pending",
    )
    ok = await extract_one(FakeSession(), item)
    assert ok
    assert item.processing_status == "extracted"
    assert item.content_md
    assert "Model Context Protocol" in item.content_md


@pytest.mark.asyncio
async def test_extract_skips_manual_with_no_url():
    item = SimpleNamespace(url=None, source_type="manual", content_md=None, processing_status="pending")
    ok = await extract_one(FakeSession(), item)
    assert ok
    assert item.processing_status == "extracted"


@pytest.mark.asyncio
async def test_extract_reuses_existing_content_without_fetch(monkeypatch):
    calls = 0

    async def fail_fetch(url):
        nonlocal calls
        calls += 1
        return None

    monkeypatch.setattr("app.processing.extract._fetch_via_trafilatura", fail_fetch)
    item = SimpleNamespace(
        source_type="web",
        url="https://example.com/article",
        content_md="already extracted " * 30,
        processing_status="pending",
    )

    ok = await extract_one(None, item)

    assert ok is True
    assert item.processing_status == "extracted"
    assert calls == 0


@pytest.mark.asyncio
async def test_extract_uses_rss_summary_fallback(monkeypatch):
    async def no_text(url):
        return None

    monkeypatch.setattr("app.processing.extract._fetch_via_trafilatura", no_text)
    monkeypatch.setattr("app.processing.extract._fetch_via_playwright", no_text)
    item = SimpleNamespace(
        source_type="rss",
        url="https://blocked.example/post",
        title="Blocked article",
        content_md=None,
        source_meta={"raw_summary": "<p>Useful <strong>feed</strong> summary &amp; context.</p>"},
        processing_status="pending",
    )

    ok = await extract_one(None, item)

    assert ok is True
    assert item.processing_status == "extracted"
    assert item.content_md == "Blocked article\n\nUseful feed summary & context."


@pytest.mark.asyncio
async def test_extract_uses_manual_title_fallback_for_unfetchable_url(monkeypatch):
    async def no_text(url):
        return None

    monkeypatch.setattr("app.processing.extract._fetch_via_trafilatura", no_text)
    monkeypatch.setattr("app.processing.extract._fetch_via_playwright", no_text)
    item = SimpleNamespace(
        source_type="manual",
        url="https://example.com/smoke",
        title="Smoke item",
        content_md=None,
        source_meta=None,
        processing_status="pending",
    )

    ok = await extract_one(None, item)

    assert ok is True
    assert item.processing_status == "extracted"
    assert item.content_md == "Smoke item\n\nURL: https://example.com/smoke"


def test_extract_html_text_uses_structured_article_fallback(monkeypatch):
    monkeypatch.setattr("app.processing.extract.trafilatura.extract", lambda *a, **kw: None)

    text = _extract_html_text(EMAIL_BODY_HTML)

    assert text is not None
    assert "Newsletter title" in text
    assert "browser automation" in text
    assert "Archive Subscribe Search" not in text
