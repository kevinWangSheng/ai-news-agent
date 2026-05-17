"""Pydantic response/request models."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ItemOut(BaseModel):
    id: int
    url: str | None
    title: str | None
    title_cn: str | None
    summary_zh: str | None
    summary_en: str | None
    recommendation: str | None
    source_type: str
    source_name: str | None
    author: str | None
    published_at: datetime | None
    ingested_at: datetime
    status: str
    processing_status: str
    quality_score: float | None
    final_score: float | None
    tags: list[str] | None
    user_note: str | None


class ItemDetail(ItemOut):
    content_md: str | None
    score_breakdown: dict[str, Any] | None
    topics: list["TopicOut"] = Field(default_factory=list)
    entities: list["EntityOut"] = Field(default_factory=list)
    related_items: list[ItemOut] = Field(default_factory=list)


class ItemPatch(BaseModel):
    status: str | None = None
    user_note: str | None = None
    tags: list[str] | None = None


class IngestRequest(BaseModel):
    url: str | None = None
    title: str | None = None
    content: str | None = None
    note: str | None = None
    tags: list[str] | None = None
    source_type: str = "manual"
    source_name: str = "manual"


class IngestResponse(BaseModel):
    item_id: int
    created: bool


class InteractionRequest(BaseModel):
    action: str
    dwell_seconds: int | None = None
    note_text: str | None = None
    highlight_text: str | None = None


class TopicOut(BaseModel):
    id: int
    slug: str
    name_zh: str
    name_en: str | None = None
    description: str | None = None
    is_pinned: bool
    item_count: int
    last_item_at: datetime | None = None


class TopicCreate(BaseModel):
    slug: str
    name_zh: str
    name_en: str | None = None
    description: str | None = None
    watch_keywords: list[str] = Field(default_factory=list)


class TopicPatch(BaseModel):
    name_zh: str | None = None
    description: str | None = None
    watch_keywords: list[str] | None = None
    is_pinned: bool | None = None


class EntityOut(BaseModel):
    id: int
    slug: str
    type: str
    name: str
    item_count: int
    last_item_at: datetime | None = None


class DigestOut(BaseModel):
    id: int
    period: str
    period_key: str
    title: str | None
    intro: str | None
    item_ids: list[int]
    generated_at: datetime


class FacetCount(BaseModel):
    value: str
    count: int


class SearchResponse(BaseModel):
    total: int
    items: list[ItemOut]
    facets: dict[str, list[FacetCount]] = Field(default_factory=dict)


class Page(BaseModel):
    items: list[ItemOut]
    next_cursor: str | None = None


class SourceOut(BaseModel):
    name: str
    source_type: str
    last_run_at: datetime | None = None
    last_success_at: datetime | None = None
    error_count: int = 0
    next_run_at: datetime | None = None
