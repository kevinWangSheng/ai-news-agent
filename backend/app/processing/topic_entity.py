"""Upsert helpers for topics / entities and their item-link tables."""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Entity, ItemEntity, ItemTopic, Topic

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    s = _SLUG_RE.sub("-", value.lower().strip()).strip("-")
    return s or "untitled"


async def upsert_topic(session: AsyncSession, slug: str, name_zh: str) -> int:
    existing = (
        await session.execute(select(Topic.id).where(Topic.slug == slug))
    ).scalar_one_or_none()
    if existing:
        return existing
    topic = Topic(slug=slug, name_zh=name_zh)
    session.add(topic)
    await session.flush()
    return topic.id


async def upsert_entity(
    session: AsyncSession, type_: str, name: str
) -> int:
    slug = slugify(f"{type_}-{name}")
    existing = (
        await session.execute(select(Entity.id).where(Entity.slug == slug))
    ).scalar_one_or_none()
    if existing:
        return existing
    entity = Entity(slug=slug, type=type_, name=name)
    session.add(entity)
    await session.flush()
    return entity.id


async def link_item_topic(session: AsyncSession, item_id: int, topic_id: int, confidence: float | None = None) -> None:
    stmt = pg_insert(ItemTopic).values(item_id=item_id, topic_id=topic_id, confidence=confidence)
    stmt = stmt.on_conflict_do_nothing(index_elements=["item_id", "topic_id"])
    await session.execute(stmt)


async def link_item_entity(session: AsyncSession, item_id: int, entity_id: int, role: str = "mentioned") -> None:
    stmt = pg_insert(ItemEntity).values(item_id=item_id, entity_id=entity_id, role=role)
    stmt = stmt.on_conflict_do_nothing(index_elements=["item_id", "entity_id", "role"])
    await session.execute(stmt)
