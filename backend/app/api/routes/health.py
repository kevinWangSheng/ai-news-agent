"""Health endpoints — consolidated from app.main inline defs."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Item
from app.db.session import get_db
from app.scoring import preferences

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    try:
        await db.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"db": "down", "error": str(exc)[:200]}


@router.get("/health/processing")
async def health_processing(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    statuses = ["pending", "extracted", "enriched", "embedded", "ready", "failed"]
    out: dict[str, int] = {}
    for st in statuses:
        n = (
            await db.execute(
                select(func.count()).select_from(Item).where(Item.processing_status == st)
            )
        ).scalar_one()
        out[st] = int(n or 0)
    return out


@router.get("/health/scoring")
async def health_scoring(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    s = get_settings()
    total = await preferences.total_interactions(db)
    return {
        "total_interactions": total,
        "cold_start_passed": total >= s.preference_cold_start_min_interactions,
        "cold_start_min": s.preference_cold_start_min_interactions,
    }
