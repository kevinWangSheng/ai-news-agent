"""Items CRUD + interactions."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.cursor import decode, encode
from app.api.schemas import (
    BulkPatchRequest,
    EntityOut,
    InteractionRequest,
    ItemLanes,
    ItemDetail,
    ItemOut,
    ItemPatch,
    Page,
    TopicOut,
)
from app.db.models import Entity, Interaction, Item, ItemEntity, ItemTopic, Topic
from app.db.session import get_db
from app.api.utils.tier import resolve_tier
from app.ranking import diversify_ranked_items

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=Page)
async def list_items(
    status: str | None = None,
    source_type: str | None = None,
    source_name: str | None = None,
    topic: str | None = Query(None, description="topic slug"),
    entity: str | None = Query(None, description="entity slug"),
    min_score: float | None = None,
    tier: str | None = None,
    since: str | None = Query(None, pattern="^(24h|7d|all)$"),
    sort: str = Query("time", pattern="^(time|score)$"),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = None,
    cursor: str | None = None,
    limit: int = Query(20, le=1000),
    db: AsyncSession = Depends(get_db),
) -> Page:
    stmt = select(Item)
    if status and status != "all":
        stmt = stmt.where(Item.status == status)
    if source_type:
        stmt = stmt.where(Item.source_type == source_type)
    if source_name:
        stmt = stmt.where(Item.source_name == source_name)
    if min_score is not None:
        stmt = stmt.where(Item.final_score >= min_score)
    if since and since != "all":
        delta = timedelta(hours=24) if since == "24h" else timedelta(days=7)
        stmt = stmt.where(Item.ingested_at >= datetime.now(timezone.utc) - delta)
    if tier:
        resolved = resolve_tier(tier)
        if resolved is not None:
            field, values = resolved
            if field == "source_type":
                stmt = stmt.where(Item.source_type.in_(values))
            else:
                stmt = stmt.where(Item.source_name.in_(values))
    if from_:
        stmt = stmt.where(Item.published_at >= from_)
    if to:
        stmt = stmt.where(Item.published_at <= to)
    if topic:
        stmt = stmt.join(ItemTopic, ItemTopic.item_id == Item.id).join(
            Topic, Topic.id == ItemTopic.topic_id
        ).where(Topic.slug == topic)
    if entity:
        stmt = stmt.join(ItemEntity, ItemEntity.item_id == Item.id).join(
            Entity, Entity.id == ItemEntity.entity_id
        ).where(Entity.slug == entity)

    cursor_data = decode(cursor)
    if cursor_data:
        ts, last_id = cursor_data
        stmt = stmt.where(
            (Item.created_at < ts) | and_(Item.created_at == ts, Item.id < last_id)
        )

    if sort == "score":
        stmt = stmt.order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
    else:
        stmt = stmt.order_by(Item.created_at.desc(), Item.id.desc())

    fetch_limit = limit + 1
    if sort == "score":
        fetch_limit = min(1000, max(limit + 1, limit * 8))
    rows = (await db.execute(stmt.limit(fetch_limit))).scalars().all()

    if sort == "score":
        rows = diversify_ranked_items(rows, limit + 1)

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = (
        encode(page_rows[-1].created_at, page_rows[-1].id) if has_more and page_rows else None
    )
    return Page(items=await _with_viewed_at(page_rows, db), next_cursor=next_cursor)


@router.post("/bulk")
async def bulk_patch(body: BulkPatchRequest, db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    ids = list(dict.fromkeys(body.ids))
    if not ids:
        return {"updated": 0}
    await db.execute(update(Item).where(Item.id.in_(ids)).values(status=body.action))
    await db.commit()
    return {"updated": len(ids)}


@router.get("/lanes", response_model=ItemLanes)
async def item_lanes(
    status: str = "inbox",
    since: str | None = Query(None, pattern="^(24h|7d|all)$"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> ItemLanes:
    base = select(Item)
    if status and status != "all":
        base = base.where(Item.status == status)
    if since and since != "all":
        delta = timedelta(hours=24) if since == "24h" else timedelta(days=7)
        base = base.where(Item.ingested_at >= datetime.now(timezone.utc) - delta)

    top_rows = (
        await db.execute(
            base.order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(min(1000, limit * 10))
        )
    ).scalars().all()
    top_signals = diversify_ranked_items(top_rows, limit)

    official_values = resolve_tier("official")[1]  # type: ignore[index]
    official_rows = (
        await db.execute(
            base.where(Item.source_name.in_(official_values))
            .order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(min(500, limit * 8))
        )
    ).scalars().all()
    official_updates = diversify_ranked_items(
        official_rows,
        limit,
        type_caps={},
        source_cap=max(2, int(limit * 0.12)),
        backfill=False,
    )

    repo_rows = (
        await db.execute(
            base.where(Item.source_type == "github")
            .order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(min(500, limit * 8))
        )
    ).scalars().all()
    repo_radar = diversify_ranked_items(
        repo_rows,
        limit,
        type_caps={},
        source_cap=max(3, int(limit * 0.18)),
        backfill=False,
    )

    return ItemLanes(
        top_signals=await _with_viewed_at(top_signals, db),
        official_updates=await _with_viewed_at(official_updates, db),
        repo_radar=await _with_viewed_at(repo_radar, db),
    )


@router.get("/{item_id}", response_model=ItemDetail)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)) -> ItemDetail:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")

    topics = (
        await db.execute(
            select(Topic).join(ItemTopic, ItemTopic.topic_id == Topic.id).where(
                ItemTopic.item_id == item_id
            )
        )
    ).scalars().all()
    entities = (
        await db.execute(
            select(Entity).join(ItemEntity, ItemEntity.entity_id == Entity.id).where(
                ItemEntity.item_id == item_id
            )
        )
    ).scalars().all()

    related: list[Item] = []
    if item.embedding is not None:
        related = (
            await db.execute(
                select(Item)
                .where(Item.id != item.id)
                .where(Item.embedding.is_not(None))
                .order_by(Item.embedding.cosine_distance(item.embedding))
                .limit(5)
            )
        ).scalars().all()

    return ItemDetail(
        **(await _with_viewed_at([item], db))[0].model_dump(),
        content_md=item.content_md,
        topics=[TopicOut.model_validate(t, from_attributes=True) for t in topics],
        entities=[EntityOut.model_validate(e, from_attributes=True) for e in entities],
        related_items=[ItemOut.model_validate(r, from_attributes=True) for r in related],
    )


@router.patch("/{item_id}", response_model=ItemOut)
async def patch_item(item_id: int, patch: ItemPatch, db: AsyncSession = Depends(get_db)) -> ItemOut:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    if patch.status is not None:
        item.status = patch.status
    if patch.user_note is not None:
        item.user_note = patch.user_note
    if patch.tags is not None:
        item.tags = patch.tags
    await db.commit()
    await db.refresh(item)
    return ItemOut.model_validate(item, from_attributes=True)


@router.delete("/{item_id}", response_model=ItemOut)
async def soft_delete(item_id: int, db: AsyncSession = Depends(get_db)) -> ItemOut:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    item.status = "trashed"
    await db.commit()
    await db.refresh(item)
    return ItemOut.model_validate(item, from_attributes=True)


@router.post("/{item_id}/interactions")
async def add_interaction(
    item_id: int, req: InteractionRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    inter = Interaction(
        item_id=item_id,
        action=req.action,
        dwell_seconds=req.dwell_seconds,
        note_text=req.note_text,
        highlight_text=req.highlight_text,
    )
    db.add(inter)
    # auto-progress item status for common actions
    if req.action == "keep":
        item.status = "kept"
    elif req.action == "archive":
        item.status = "archived"
    elif req.action == "trash":
        item.status = "trashed"
    if req.note_text:
        item.user_note = req.note_text
    await db.commit()
    await db.refresh(inter)
    return {"id": inter.id}


async def _with_viewed_at(items: list[Item], db: AsyncSession) -> list[ItemOut]:
    if not items:
        return []
    ids = [i.id for i in items]
    viewed_rows = (
        await db.execute(
            select(Interaction.item_id, func.max(Interaction.created_at))
            .where(Interaction.item_id.in_(ids))
            .where(Interaction.action == "view")
            .group_by(Interaction.item_id)
        )
    ).all()
    viewed = {item_id: ts for item_id, ts in viewed_rows}
    out: list[ItemOut] = []
    for item in items:
        data = ItemOut.model_validate(item, from_attributes=True).model_dump()
        data["viewed_at"] = viewed.get(item.id)
        out.append(ItemOut(**data))
    return out
