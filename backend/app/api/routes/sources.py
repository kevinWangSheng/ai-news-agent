"""Sources listing + manual trigger."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SourceOut
from app.db.models import IngestionError, Item
from app.db.session import get_db
from app.ingestion.run import build_sources, load_config, load_topics, run_source

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)) -> list[SourceOut]:
    sources_by_kind = build_sources(load_config(), load_topics())
    since = datetime.now(timezone.utc) - timedelta(days=7)
    out: list[SourceOut] = []
    for kind, sources in sources_by_kind.items():
        for s in sources:
            errors = (
                await db.execute(
                    select(func.count())
                    .select_from(IngestionError)
                    .where(IngestionError.source_type == s.source_type)
                    .where(IngestionError.source_name == s.name)
                    .where(IngestionError.created_at >= since)
                )
            ).scalar_one()
            last = (
                await db.execute(
                    select(func.max(Item.ingested_at))
                    .where(Item.source_type == s.source_type)
                    .where(Item.source_name == s.name)
                )
            ).scalar_one()
            out.append(
                SourceOut(
                    name=s.name,
                    source_type=s.source_type,
                    last_run_at=None,  # 012 fills next_run / last_run from scheduler
                    last_success_at=last,
                    error_count=int(errors or 0),
                )
            )
    return out


@router.post("/{name}/trigger")
async def trigger_source(name: str, background: BackgroundTasks) -> dict:
    sources_by_kind = build_sources(load_config(), load_topics())
    target = None
    for sources in sources_by_kind.values():
        for s in sources:
            if s.name == name:
                target = s
                break
        if target:
            break
    if target is None:
        raise HTTPException(404, f"source {name} not found")
    background.add_task(run_source, target)
    return {"queued": True, "source": name}
