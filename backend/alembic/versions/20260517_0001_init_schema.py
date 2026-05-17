"""init schema — items / topics / entities / interactions / digests + extensions + triggers + indexes.

Revision ID: 0001_init
Revises:
Create Date: 2026-05-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from app.config import get_settings

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEARCH_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION items_search_vector_trigger() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('simple', coalesce(NEW.title_cn,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(NEW.title,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(NEW.summary_zh,'')), 'B') ||
    setweight(to_tsvector('simple', coalesce(left(NEW.content_md,2000),'')), 'C') ||
    setweight(to_tsvector('simple', coalesce(array_to_string(NEW.tags,' '),'')), 'B');
  RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

TOPIC_COUNT_FN = """
CREATE OR REPLACE FUNCTION bump_topic_count() RETURNS trigger AS $$
BEGIN
  IF (TG_OP = 'INSERT') THEN
    UPDATE topics SET item_count = item_count + 1, last_item_at = now()
      WHERE id = NEW.topic_id;
    RETURN NEW;
  ELSIF (TG_OP = 'DELETE') THEN
    UPDATE topics SET item_count = GREATEST(item_count - 1, 0)
      WHERE id = OLD.topic_id;
    RETURN OLD;
  END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

ENTITY_COUNT_FN = """
CREATE OR REPLACE FUNCTION bump_entity_count() RETURNS trigger AS $$
BEGIN
  IF (TG_OP = 'INSERT') THEN
    UPDATE entities SET item_count = item_count + 1, last_item_at = now()
      WHERE id = NEW.entity_id;
    RETURN NEW;
  ELSIF (TG_OP = 'DELETE') THEN
    UPDATE entities SET item_count = GREATEST(item_count - 1, 0)
      WHERE id = OLD.entity_id;
    RETURN OLD;
  END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("url", sa.Text()),
        sa.Column("url_normalized", sa.Text(), unique=True),
        sa.Column("title", sa.Text()),
        sa.Column("title_cn", sa.Text()),
        sa.Column("content_md", sa.Text()),
        sa.Column("summary_zh", sa.Text()),
        sa.Column("summary_en", sa.Text()),
        sa.Column("recommendation", sa.Text()),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_name", sa.Text()),
        sa.Column("source_meta", JSONB()),
        sa.Column("author", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.Text(), nullable=False, server_default="inbox"),
        sa.Column("processing_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("processing_attempts", sa.Integer(), server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.Column("quality_score", sa.Numeric(3, 1)),
        sa.Column("final_score", sa.Numeric(3, 1)),
        sa.Column("score_breakdown", JSONB()),
        sa.Column("tags", sa.ARRAY(sa.Text())),
        sa.Column("embedding", Vector(1024)),
        sa.Column("search_vector", TSVECTOR()),
        sa.Column("user_note", sa.Text()),
        sa.Column("user_highlight", sa.ARRAY(sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_items_status", "items", ["status"])
    op.create_index("idx_items_source", "items", ["source_type", "source_name"])
    op.create_index("idx_items_published", "items", ["published_at"])
    op.create_index("idx_items_score", "items", ["final_score"])
    op.create_index("idx_items_search", "items", ["search_vector"], postgresql_using="gin")

    s = get_settings()
    op.execute(
        f"CREATE INDEX idx_items_embedding ON items USING hnsw (embedding vector_cosine_ops) "
        f"WITH (m = {s.hnsw_m}, ef_construction = {s.hnsw_ef_construction})"
    )

    op.create_table(
        "topics",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.Text(), unique=True, nullable=False),
        sa.Column("name_zh", sa.Text(), nullable=False),
        sa.Column("name_en", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("watch_keywords", sa.ARRAY(sa.Text())),
        sa.Column("is_pinned", sa.Boolean(), server_default="false"),
        sa.Column("item_count", sa.Integer(), server_default="0"),
        sa.Column("last_item_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.Text(), unique=True, nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("aliases", sa.ARRAY(sa.Text())),
        sa.Column("canonical_url", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("metadata", JSONB()),
        sa.Column("item_count", sa.Integer(), server_default="0"),
        sa.Column("last_item_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "item_topics",
        sa.Column("item_id", sa.BigInteger(), sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("topic_id", sa.BigInteger(), sa.ForeignKey("topics.id", ondelete="CASCADE")),
        sa.Column("confidence", sa.Numeric(3, 2)),
        sa.PrimaryKeyConstraint("item_id", "topic_id"),
    )
    op.create_table(
        "item_entities",
        sa.Column("item_id", sa.BigInteger(), sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("entities.id", ondelete="CASCADE")),
        sa.Column("role", sa.Text()),
        sa.PrimaryKeyConstraint("item_id", "entity_id", "role"),
    )

    op.create_table(
        "interactions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.BigInteger(), sa.ForeignKey("items.id", ondelete="CASCADE")),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("dwell_seconds", sa.Integer()),
        sa.Column("note_text", sa.Text()),
        sa.Column("highlight_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_interactions_item", "interactions", ["item_id", "created_at"])
    op.create_index("idx_interactions_action", "interactions", ["action", "created_at"])

    op.create_table(
        "digests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("intro", sa.Text()),
        sa.Column("item_ids", sa.ARRAY(sa.BigInteger())),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("period", "period_key", name="uq_digests_period_period_key"),
    )

    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_type", sa.Text()),
        sa.Column("source_name", sa.Text()),
        sa.Column("url", sa.Text()),
        sa.Column("error_type", sa.Text()),
        sa.Column("error_msg", sa.Text()),
        sa.Column("raw", JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.execute(SEARCH_TRIGGER_FN)
    op.execute(
        "CREATE TRIGGER items_search_vector_update "
        "BEFORE INSERT OR UPDATE ON items "
        "FOR EACH ROW EXECUTE FUNCTION items_search_vector_trigger();"
    )

    op.execute(TOPIC_COUNT_FN)
    op.execute(
        "CREATE TRIGGER item_topics_count_trigger "
        "AFTER INSERT OR DELETE ON item_topics "
        "FOR EACH ROW EXECUTE FUNCTION bump_topic_count();"
    )

    op.execute(ENTITY_COUNT_FN)
    op.execute(
        "CREATE TRIGGER item_entities_count_trigger "
        "AFTER INSERT OR DELETE ON item_entities "
        "FOR EACH ROW EXECUTE FUNCTION bump_entity_count();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS item_entities_count_trigger ON item_entities")
    op.execute("DROP TRIGGER IF EXISTS item_topics_count_trigger ON item_topics")
    op.execute("DROP TRIGGER IF EXISTS items_search_vector_update ON items")
    op.execute("DROP FUNCTION IF EXISTS bump_entity_count()")
    op.execute("DROP FUNCTION IF EXISTS bump_topic_count()")
    op.execute("DROP FUNCTION IF EXISTS items_search_vector_trigger()")

    op.drop_table("ingestion_errors")
    op.drop_table("digests")
    op.drop_index("idx_interactions_action", table_name="interactions")
    op.drop_index("idx_interactions_item", table_name="interactions")
    op.drop_table("interactions")
    op.drop_table("item_entities")
    op.drop_table("item_topics")
    op.drop_table("entities")
    op.drop_table("topics")
    op.drop_index("idx_items_embedding", table_name="items")
    op.drop_index("idx_items_search", table_name="items")
    op.drop_index("idx_items_score", table_name="items")
    op.drop_index("idx_items_published", table_name="items")
    op.drop_index("idx_items_source", table_name="items")
    op.drop_index("idx_items_status", table_name="items")
    op.drop_table("items")
