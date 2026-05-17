"""String enums used as TEXT columns in DB (kept as Python enums for type safety)."""
from enum import StrEnum


class ItemStatus(StrEnum):
    inbox = "inbox"
    kept = "kept"
    archived = "archived"
    trashed = "trashed"


class ProcessingStatus(StrEnum):
    pending = "pending"
    extracted = "extracted"
    enriched = "enriched"
    embedded = "embedded"
    ready = "ready"
    failed = "failed"


class SourceType(StrEnum):
    manual = "manual"
    rss = "rss"
    github = "github"
    exa_search = "exa_search"
    twitter = "twitter"
    chinese_platform = "chinese_platform"


class InteractionAction(StrEnum):
    view = "view"
    keep = "keep"
    archive = "archive"
    trash = "trash"
    highlight = "highlight"
    note = "note"
    share = "share"


class EntityType(StrEnum):
    person = "person"
    company = "company"
    project = "project"
    model = "model"
    paper = "paper"
