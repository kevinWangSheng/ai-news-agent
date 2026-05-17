"""Source protocol + RawItem DTO."""
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class RawItem(BaseModel):
    url: str | None = None
    title: str | None = None
    source_type: str
    source_name: str
    source_meta: dict[str, Any] = Field(default_factory=dict)
    author: str | None = None
    published_at: datetime | None = None
    content_html: str | None = None
    content_md: str | None = None


class Source(Protocol):
    name: str
    source_type: str

    async def fetch(self) -> list[RawItem]: ...
