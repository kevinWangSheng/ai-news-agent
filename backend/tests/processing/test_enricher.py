"""Unit-level enricher test that mocks Claude to return fixed JSON."""
from types import SimpleNamespace

import pytest

from app.processing import enricher


FAKE_RESPONSE = {
    "title_cn": "测试标题",
    "summary_zh": "概要",
    "tags": ["mcp", "agent"],
    "entities": [{"type": "project", "name": "MCP", "role": "subject"}],
    "quality_score": 8,
    "recommendation": "值得读",
}


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, x):
        self.added.append(x)

    async def flush(self):
        pass

    async def execute(self, stmt):
        class R:
            def scalar_one_or_none(self):
                return None

        return R()


@pytest.mark.asyncio
async def test_enricher_parses_json_and_writes_fields(monkeypatch):
    async def fake_call(payload):
        return FAKE_RESPONSE

    async def fake_link(session, item, parsed):
        return None

    monkeypatch.setattr(enricher, "_call_claude", fake_call)
    monkeypatch.setattr(enricher, "_link_topics_entities", fake_link)

    item = SimpleNamespace(
        id=1,
        title="Foo",
        url="https://example.com/x",
        content_md="...",
        source_name="rss",
        status="inbox",
        processing_status="extracted",
        score_breakdown=None,
        title_cn=None,
        summary_zh=None,
        summary_en=None,
        tags=None,
        recommendation=None,
        quality_score=None,
    )

    ok = await enricher.enrich_one(FakeSession(), item)
    assert ok
    assert item.title_cn == "测试标题"
    assert item.tags == ["mcp", "agent"]
    assert item.quality_score == 8
    assert item.processing_status == "enriched"


@pytest.mark.asyncio
async def test_enricher_archives_on_exclude(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("EXCLUDE_KEYWORDS", '["image generation"]')

    s = get_settings()
    assert s.exclude_keywords == ["image generation"]

    item = SimpleNamespace(
        id=1,
        title="A guide to image generation",
        content_md="midjourney usage",
        status="inbox",
        processing_status="extracted",
        score_breakdown=None,
        title_cn=None,
        summary_zh=None,
        summary_en=None,
        tags=None,
        recommendation=None,
        quality_score=None,
    )
    ok = await enricher.enrich_one(FakeSession(), item)
    assert ok
    assert item.status == "archived"
    assert item.processing_status == "ready"
    assert "image generation" in item.score_breakdown["exclude_keywords"]

    get_settings.cache_clear()


def test_parse_json_object_accepts_fenced_json():
    text = """```json
{"title_cn":"标题","tags":["agent"]}
```"""

    assert enricher._parse_json_object(text) == {"title_cn": "标题", "tags": ["agent"]}


def test_parse_json_object_extracts_surrounding_text():
    text = 'Here is JSON:\n{"title_cn":"标题","quality_score":8}\nThanks'

    assert enricher._parse_json_object(text) == {"title_cn": "标题", "quality_score": 8}


def test_parse_json_object_rejects_invalid_json():
    text = '{"summary_zh":"之前的"不干预"政策"}'

    assert enricher._parse_json_object(text) is None
