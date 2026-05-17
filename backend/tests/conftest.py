"""Shared pytest fixtures — testcontainers-managed postgres + alembic upgrade head."""
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer

BACKEND_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def pg_container() -> PostgresContainer:
    container = PostgresContainer("pgvector/pgvector:pg16", username="hub", password="hub", dbname="hub")
    container.start()
    yield container
    container.stop()


@pytest_asyncio.fixture(scope="session")
async def pg_engine(pg_container: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    sync_url = pg_container.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg").replace(
        "postgresql://", "postgresql+asyncpg://"
    )

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", async_url)
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(cfg, "head")

    engine = create_async_engine(async_url, pool_pre_ping=True)
    yield engine
    await engine.dispose()
