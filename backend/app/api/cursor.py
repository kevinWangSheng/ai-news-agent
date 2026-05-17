"""(created_at_iso, id) cursor encoding for stable pagination."""
from __future__ import annotations

import base64
import json
from datetime import datetime


def encode(created_at: datetime, item_id: int) -> str:
    raw = json.dumps([created_at.isoformat(), item_id])
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode(cursor: str | None) -> tuple[datetime, int] | None:
    if not cursor:
        return None
    pad = "=" * ((4 - len(cursor) % 4) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor + pad).decode()
        ts_iso, item_id = json.loads(raw)
        return datetime.fromisoformat(ts_iso), int(item_id)
    except (ValueError, json.JSONDecodeError):
        return None
