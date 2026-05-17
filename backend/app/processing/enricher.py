"""Stage 2: Claude enrichment → title_cn / summary / tags / entities / quality_score.

Uses prompt cache via shared anthropic client; system prompt is fixed and cache-controlled.
Honors exclude_keywords (skip LLM, archive directly).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Item
from app.llm.client import get_claude
from app.processing.keyword_match import matched_keywords
from app.processing.topic_entity import (
    link_item_entity,
    link_item_topic,
    slugify,
    upsert_entity,
    upsert_topic,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是 AI Agent 领域的资深技术编辑,熟悉 LLM、Agent 框架、协议(MCP、A2A、tool use、function calling)、多智能体架构。
对单条信息条目做加工,输出严格 JSON,字段:
- title_cn(str)
- summary_zh(str, <=200 字)
- summary_en(str, <=120 words, 可空)
- tags(list[str], 3-7 个英文小写连字符)
- entities(list[{type: person|company|project|model|paper, name: str, role?: str}])
- quality_score(int 1-10, 评估专业度+新颖度+对 Agent 领域的相关性)
- recommendation(str, 一句话推荐理由)
不要解释,只输出 JSON。"""


async def enrich_one(session: AsyncSession, item: Item) -> bool:
    s = get_settings()

    text = (item.title or "") + "\n\n" + (item.content_md or "")
    if s.exclude_keywords:
        hits = matched_keywords(s.exclude_keywords, text)
        if hits:
            item.status = "archived"
            item.processing_status = "ready"
            item.score_breakdown = {"exclude_keywords": hits}
            logger.info("item=%s archived by exclude=%s", item.id, hits)
            return True

    payload = json.dumps(
        {
            "title": item.title,
            "url": item.url,
            "source": item.source_name,
            "content": (item.content_md or "")[:6000],
        },
        ensure_ascii=False,
    )
    parsed = await _call_claude(payload)
    if parsed is None:
        return False

    item.title_cn = parsed.get("title_cn") or item.title
    item.summary_zh = parsed.get("summary_zh")
    item.summary_en = parsed.get("summary_en")
    item.tags = parsed.get("tags") or []
    item.recommendation = parsed.get("recommendation")
    qs = parsed.get("quality_score")
    if isinstance(qs, (int, float)):
        item.quality_score = float(qs)

    await _link_topics_entities(session, item, parsed)

    item.processing_status = "enriched"
    return True


async def _call_claude(payload: str) -> dict[str, Any] | None:
    s = get_settings()
    if not s.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set; skipping enricher LLM call")
        return None
    client = get_claude()
    try:
        resp = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": payload}],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("claude enrich call failed: %s", exc)
        return None
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    logger.warning("could not parse claude JSON: %s", text[:200])
    return None


async def _link_topics_entities(session: AsyncSession, item: Item, parsed: dict) -> None:
    for tag in item.tags or []:
        topic_id = await upsert_topic(session, slug=slugify(tag), name_zh=tag)
        await link_item_topic(session, item.id, topic_id, confidence=0.8)

    for ent in parsed.get("entities") or []:
        if not isinstance(ent, dict) or not ent.get("name"):
            continue
        entity_id = await upsert_entity(
            session, type_=ent.get("type") or "project", name=ent["name"]
        )
        await link_item_entity(session, item.id, entity_id, role=ent.get("role") or "mentioned")
