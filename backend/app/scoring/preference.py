"""Helper used by 004 finalize.py — wraps engine.score_item against current signals.

Re-fetches signals on each call; recompute.py caches signals across a batch.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Entity, Item, ItemEntity, ItemTopic, Topic
from app.scoring import preferences
from app.scoring.engine import ScoreBreakdown, score_item


async def _slugs_for_item(session: AsyncSession, item_id: int) -> tuple[list[str], list[str]]:
    tag_slugs = (
        await session.execute(
            select(Topic.slug).join(ItemTopic, ItemTopic.topic_id == Topic.id).where(
                ItemTopic.item_id == item_id
            )
        )
    ).scalars().all()
    entity_slugs = (
        await session.execute(
            select(Entity.slug).join(ItemEntity, ItemEntity.entity_id == Entity.id).where(
                ItemEntity.item_id == item_id
            )
        )
    ).scalars().all()
    return list(tag_slugs), list(entity_slugs)


async def compute_preference_breakdown(session: AsyncSession, item: Item) -> ScoreBreakdown:
    s = get_settings()
    tag_sigs = await preferences.compute_tag_signals(session)
    entity_sigs = await preferences.compute_entity_signals(session)
    source_sigs = await preferences.compute_source_signals(session)
    total = await preferences.total_interactions(session)
    tag_slugs, entity_slugs = await _slugs_for_item(session, item.id)
    return score_item(
        item,
        tag_signals=tag_sigs,
        entity_signals=entity_sigs,
        source_signals=source_sigs,
        total_interactions_count=total,
        item_tag_slugs=tag_slugs,
        item_entity_slugs=entity_slugs,
        focus_keywords=s.focus_keywords,
    )


async def compute_preference_delta(session: AsyncSession, item: Item) -> tuple[float, dict]:
    b = await compute_preference_breakdown(session, item)
    delta = b.final - b.base
    return delta, b.to_dict()
