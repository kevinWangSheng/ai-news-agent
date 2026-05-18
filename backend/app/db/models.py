"""SQLAlchemy models — mirror of openspec/specs/storage.md."""
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    url: Mapped[str | None] = mapped_column(Text)
    url_normalized: Mapped[str | None] = mapped_column(Text, unique=True)
    title: Mapped[str | None] = mapped_column(Text)
    title_cn: Mapped[str | None] = mapped_column(Text)
    content_md: Mapped[str | None] = mapped_column(Text)
    summary_zh: Mapped[str | None] = mapped_column(Text)
    summary_en: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(Text)
    source_meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    author: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="inbox")
    processing_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="pending"
    )
    processing_attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text)
    quality_score: Mapped[float | None] = mapped_column(Numeric(3, 1))
    final_score: Mapped[float | None] = mapped_column(Numeric(3, 1))
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    search_vector: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)
    user_note: Mapped[str | None] = mapped_column(Text)
    user_highlight: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_items_status", "status"),
        Index("idx_items_source", "source_type", "source_name"),
        Index("idx_items_published", "published_at"),
        Index("idx_items_score", "final_score"),
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name_zh: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    watch_keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    is_pinned: Mapped[bool] = mapped_column(Boolean, server_default="false")
    item_count: Mapped[int] = mapped_column(Integer, server_default="0")
    last_item_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    canonical_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    entity_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    item_count: Mapped[int] = mapped_column(Integer, server_default="0")
    last_item_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ItemTopic(Base):
    __tablename__ = "item_topics"

    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE")
    )
    topic_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topics.id", ondelete="CASCADE")
    )
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2))

    __table_args__ = (PrimaryKeyConstraint("item_id", "topic_id"),)


class ItemEntity(Base):
    __tablename__ = "item_entities"

    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE")
    )
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(Text)

    __table_args__ = (PrimaryKeyConstraint("item_id", "entity_id", "role"),)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE")
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    dwell_seconds: Mapped[int | None] = mapped_column(Integer)
    note_text: Mapped[str | None] = mapped_column(Text)
    highlight_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_interactions_item", "item_id", "created_at"),
        Index("idx_interactions_action", "action", "created_at"),
    )


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    period_key: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    intro: Mapped[str | None] = mapped_column(Text)
    item_ids: Mapped[list[int] | None] = mapped_column(ARRAY(BigInteger))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("period", "period_key", name="uq_digests_period_period_key"),)


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_type: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(Text)
    error_msg: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
