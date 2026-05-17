"""POST /api/ingest — manual feed entry-point shared by bookmarklet + CLI."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import IngestRequest, IngestResponse
from app.db.session import get_db
from app.ingestion.base import RawItem
from app.ingestion.service import IngestionService

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, db: AsyncSession = Depends(get_db)) -> IngestResponse:
    raw = RawItem(
        url=req.url,
        title=req.title or (req.url and "")  # title fallback to url-derived
        or (req.content[:80] if req.content else None),
        source_type=req.source_type,
        source_name=req.source_name,
        content_md=req.content,
        source_meta={"note": req.note, "tags": req.tags} if (req.note or req.tags) else {},
    )
    svc = IngestionService(db)
    item, created = await svc.create_item(raw)
    if req.note:
        item.user_note = req.note
    if req.tags:
        item.tags = req.tags
    await db.commit()
    return IngestResponse(item_id=item.id, created=created)
