"""FastAPI entry point — wires all routes."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import digests, entities, health, ingest, items, search, sources, topics
from app.config import get_settings
from app.db.session import get_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "DB ping failed (%s). 请先 `alembic upgrade head` 并确认 DATABASE_URL 正确。", exc
        )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ai-agent-hub", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for r in (health, ingest, items, search, topics, entities, digests, sources):
        app.include_router(r.router)
    return app


app = create_app()
