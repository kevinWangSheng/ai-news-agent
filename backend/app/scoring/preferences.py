"""Aggregate interaction signals — keep_rate per tag / entity / source."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Entity, Interaction, Item, ItemEntity, ItemTopic, Topic


@dataclass
class Signal:
    keep_rate: float
    count: int


KEEP_ACTIONS = ("keep", "highlight", "note")
DROP_ACTIONS = ("archive", "trash")


def _since(window_days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=window_days)


async def total_interactions(session: AsyncSession, window_days: int = 30) -> int:
    n = (
        await session.execute(
            select(func.count())
            .select_from(Interaction)
            .where(Interaction.created_at >= _since(window_days))
        )
    ).scalar_one()
    return int(n or 0)


async def compute_tag_signals(session: AsyncSession, window_days: int = 30) -> dict[str, Signal]:
    rows = (
        await session.execute(
            select(
                Topic.slug,
                func.count(Interaction.id).label("total"),
                func.sum(
                    func.cast(Interaction.action.in_(KEEP_ACTIONS), func.Integer)
                ).label("kept"),
            )
            .select_from(Interaction)
            .join(Item, Item.id == Interaction.item_id)
            .join(ItemTopic, ItemTopic.item_id == Item.id)
            .join(Topic, Topic.id == ItemTopic.topic_id)
            .where(Interaction.created_at >= _since(window_days))
            .group_by(Topic.slug)
        )
    ).all()
    out: dict[str, Signal] = {}
    for slug, total, kept in rows:
        total = int(total or 0)
        kept = int(kept or 0)
        out[slug] = Signal(keep_rate=(kept / total) if total else 0.0, count=total)
    return out


async def compute_entity_signals(session: AsyncSession, window_days: int = 30) -> dict[str, Signal]:
    rows = (
        await session.execute(
            select(
                Entity.slug,
                func.count(Interaction.id),
                func.sum(func.cast(Interaction.action.in_(KEEP_ACTIONS), func.Integer)),
            )
            .select_from(Interaction)
            .join(Item, Item.id == Interaction.item_id)
            .join(ItemEntity, ItemEntity.item_id == Item.id)
            .join(Entity, Entity.id == ItemEntity.entity_id)
            .where(Interaction.created_at >= _since(window_days))
            .group_by(Entity.slug)
        )
    ).all()
    return {
        slug: Signal(keep_rate=(kept / total) if total else 0.0, count=int(total or 0))
        for slug, total, kept in rows
    }


async def compute_source_signals(session: AsyncSession, window_days: int = 30) -> dict[str, Signal]:
    rows = (
        await session.execute(
            select(
                Item.source_name,
                func.count(Interaction.id),
                func.sum(func.cast(Interaction.action.in_(KEEP_ACTIONS), func.Integer)),
            )
            .select_from(Interaction)
            .join(Item, Item.id == Interaction.item_id)
            .where(Interaction.created_at >= _since(window_days))
            .group_by(Item.source_name)
        )
    ).all()
    return {
        (name or ""): Signal(
            keep_rate=(kept / total) if total else 0.0, count=int(total or 0)
        )
        for name, total, kept in rows
    }
