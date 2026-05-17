"""LLM-driven digest generation. Picks top-N ready items by final_score, writes a digest row.

Intro generation uses Claude via shared get_claude(); skipped if no API key.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import get_settings
from app.db.models import Digest, Item
from app.db.session import get_session_factory
from app.llm.client import get_claude

logger = logging.getLogger(__name__)


def _period_window(period: str) -> tuple[datetime, datetime, str]:
    now = datetime.now(timezone.utc)
    if period == "daily":
        start = now - timedelta(days=1)
        key = now.strftime("%Y-%m-%d")
    else:  # weekly
        start = now - timedelta(days=7)
        iso_year, iso_week, _ = now.isocalendar()
        key = f"{iso_year}-W{iso_week:02d}"
    return start, now, key


async def _intro_via_llm(items: list[Item]) -> str | None:
    s = get_settings()
    if not s.anthropic_api_key or not items:
        return None
    try:
        bullets = "\n".join(
            f"- [{i.final_score:.1f}] {i.title_cn or i.title}: {(i.summary_zh or '')[:120]}"
            for i in items[:15]
        )
        client = get_claude()
        resp = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "用一段不超过 150 字的中文,概括下面这批 AI Agent 领域条目的整体趋势"
                        "(不要逐条复述,提取共性):\n\n" + bullets
                    ),
                }
            ],
        )
        return "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("digest intro LLM failed: %s", exc)
        return None


async def generate_digest(period: str = "daily") -> dict:
    s = get_settings()
    start, _now, key = _period_window(period)
    factory = get_session_factory()

    async with factory() as session:
        items = (
            await session.execute(
                select(Item)
                .where(Item.processing_status == "ready")
                .where(Item.status != "trashed")
                .where(Item.final_score >= s.digest_score_threshold)
                .where(Item.ingested_at >= start)
                .order_by(Item.final_score.desc().nullslast())
                .limit(15)
            )
        ).scalars().all()

        if not items:
            return {"period": period, "key": key, "selected": 0, "skipped": True}

        intro = await _intro_via_llm(items)
        item_ids = [i.id for i in items]
        title = f"{period.capitalize()} · {key} · 共 {len(items)} 条"

        stmt = pg_insert(Digest).values(
            period=period,
            period_key=key,
            title=title,
            intro=intro,
            item_ids=item_ids,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_digests_period_period_key",
            set_={"title": title, "intro": intro, "item_ids": item_ids, "generated_at": datetime.now(timezone.utc)},
        )
        await session.execute(stmt)
        await session.commit()

    return {"period": period, "key": key, "selected": len(items)}
