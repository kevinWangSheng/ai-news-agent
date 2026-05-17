"""Smoke-test the schema: insert items + topics + interactions, verify triggers fire."""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_search_vector_trigger(pg_engine):
    async with pg_engine.begin() as conn:
        await conn.execute(text("DELETE FROM items"))
        await conn.execute(
            text(
                "INSERT INTO items (title_cn, summary_zh, source_type, tags) "
                "VALUES ('多智能体协作', 'agentic workflow 实战', 'manual', ARRAY['mcp','agent'])"
            )
        )
        row = (
            await conn.execute(text("SELECT search_vector::text FROM items LIMIT 1"))
        ).scalar_one()
    assert row and "多" in row or "mcp" in row


@pytest.mark.asyncio
async def test_topic_item_count_trigger(pg_engine):
    async with pg_engine.begin() as conn:
        await conn.execute(text("DELETE FROM item_topics"))
        await conn.execute(text("DELETE FROM topics"))
        await conn.execute(text("DELETE FROM items"))

        item_id = (
            await conn.execute(
                text(
                    "INSERT INTO items (title, source_type) VALUES ('t', 'manual') RETURNING id"
                )
            )
        ).scalar_one()
        topic_id = (
            await conn.execute(
                text("INSERT INTO topics (slug, name_zh) VALUES ('mcp', 'MCP') RETURNING id")
            )
        ).scalar_one()
        await conn.execute(
            text("INSERT INTO item_topics (item_id, topic_id, confidence) VALUES (:i, :t, 1.0)"),
            {"i": item_id, "t": topic_id},
        )
        count = (
            await conn.execute(text("SELECT item_count FROM topics WHERE id = :t"), {"t": topic_id})
        ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_interactions_insert(pg_engine):
    async with pg_engine.begin() as conn:
        await conn.execute(text("DELETE FROM interactions"))
        await conn.execute(text("DELETE FROM items"))
        item_id = (
            await conn.execute(
                text(
                    "INSERT INTO items (title, source_type) VALUES ('t', 'manual') RETURNING id"
                )
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO interactions (item_id, action, dwell_seconds) VALUES (:i, 'view', 30)"
            ),
            {"i": item_id},
        )
        n = (await conn.execute(text("SELECT count(*) FROM interactions"))).scalar_one()
    assert n == 1
