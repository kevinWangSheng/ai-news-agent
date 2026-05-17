"""Batch re-score all (or recent) ready items, sharing one signal snapshot."""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Entity, Item, ItemEntity, ItemTopic, Topic
from app.db.session import get_session_factory
from app.scoring import preferences
from app.scoring.engine import score_item

logger = logging.getLogger(__name__)


_SINCE_RE = re.compile(r"^(\d+)([dh])$")


def parse_since(s: str | None) -> datetime | None:
    if not s:
        return None
    m = _SINCE_RE.match(s)
    if not m:
        raise ValueError(f"unsupported --since spec: {s}")
    n, unit = int(m.group(1)), m.group(2)
    delta = timedelta(days=n) if unit == "d" else timedelta(hours=n)
    return datetime.now(timezone.utc) - delta


async def _slugs_for_items(session: AsyncSession, item_ids: list[int]):
    rows_t = (
        await session.execute(
            select(ItemTopic.item_id, Topic.slug).join(Topic, Topic.id == ItemTopic.topic_id).where(
                ItemTopic.item_id.in_(item_ids)
            )
        )
    ).all()
    rows_e = (
        await session.execute(
            select(ItemEntity.item_id, Entity.slug).join(Entity, Entity.id == ItemEntity.entity_id).where(
                ItemEntity.item_id.in_(item_ids)
            )
        )
    ).all()
    tag_map: dict[int, list[str]] = {}
    ent_map: dict[int, list[str]] = {}
    for iid, slug in rows_t:
        tag_map.setdefault(iid, []).append(slug)
    for iid, slug in rows_e:
        ent_map.setdefault(iid, []).append(slug)
    return tag_map, ent_map


async def recompute(since: datetime | None = None, batch_size: int = 500) -> int:
    s = get_settings()
    factory = get_session_factory()
    n_updated = 0
    async with factory() as session:
        tag_sigs = await preferences.compute_tag_signals(session)
        entity_sigs = await preferences.compute_entity_signals(session)
        source_sigs = await preferences.compute_source_signals(session)
        total = await preferences.total_interactions(session)

        stmt = select(Item).where(Item.processing_status == "ready")
        if since:
            stmt = stmt.where(Item.created_at >= since)

        offset = 0
        while True:
            page = (
                await session.execute(stmt.limit(batch_size).offset(offset))
            ).scalars().all()
            if not page:
                break
            tag_map, ent_map = await _slugs_for_items(session, [it.id for it in page])
            for item in page:
                b = score_item(
                    item,
                    tag_signals=tag_sigs,
                    entity_signals=entity_sigs,
                    source_signals=source_sigs,
                    total_interactions_count=total,
                    item_tag_slugs=tag_map.get(item.id, item.tags or []),
                    item_entity_slugs=ent_map.get(item.id, []),
                    focus_keywords=s.focus_keywords,
                )
                item.final_score = b.final
                item.score_breakdown = b.to_dict()
                n_updated += 1
            await session.commit()
            offset += batch_size
    return n_updated


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--since", type=str, help="e.g. 7d / 24h")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    since = parse_since(args.since) if args.since else None
    n = asyncio.run(recompute(since=since))
    logger.info("recomputed %d items", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
