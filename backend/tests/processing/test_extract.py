"""Unit-level extract test using static HTML via MockTransport."""
from datetime import datetime
from types import SimpleNamespace

import httpx
import pytest

from app.processing.extract import extract_one


HTML = """<html><body><article>
<h1>An article about MCP</h1>
<p>Model Context Protocol is a protocol for LLM tools.</p>
</article></body></html>"""


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
