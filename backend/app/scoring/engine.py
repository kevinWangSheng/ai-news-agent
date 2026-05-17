"""Pure scoring math + cold-start gate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import get_settings
from app.scoring.preferences import Signal


@dataclass
class ScoreBreakdown:
    base: float
    tag_boost: float
    entity_boost: float
    source_boost: float
    time_decay: float
    final: float
    cold_start: bool
    focus_hits: list[str]

    def to_dict(self) -> dict:
        return {
            "base": self.base,
            "tag_boost": self.tag_boost,
            "entity_boost": self.entity_boost,
            "source_boost": self.source_boost,
            "time_decay": self.time_decay,
            "final": self.final,
            "cold_start": self.cold_start,
            "focus_hits": self.focus_hits,
        }


def _avg_boost(slugs: list[str] | None, signals: dict[str, Signal]) -> float:
    if not slugs:
        return 0.0
    deltas = []
    for s in slugs:
        sig = signals.get(s)
        if sig is None or sig.count == 0:
            continue
        deltas.append(max(-1.0, min(2.0, sig.keep_rate * 2 - 1)))
    return sum(deltas) / max(1, len(deltas))


def _time_decay(published_at: datetime | None) -> float:
    if not published_at:
        return 0.0
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - published_at).total_seconds() / 86400
    return max(0.0, 1.0 - age_days / 30.0)


def score_item(
    item,
    tag_signals: dict[str, Signal],
    entity_signals: dict[str, Signal],
    source_signals: dict[str, Signal],
    total_interactions_count: int,
    item_tag_slugs: list[str] | None = None,
    item_entity_slugs: list[str] | None = None,
    focus_keywords: list[str] | None = None,
) -> ScoreBreakdown:
    s = get_settings()
    cold_start = total_interactions_count < s.preference_cold_start_min_interactions
    base = float(item.quality_score or 0)

    tag_boost = 0.0 if cold_start else _avg_boost(item_tag_slugs or item.tags, tag_signals)
    entity_boost = 0.0 if cold_start else _avg_boost(item_entity_slugs, entity_signals)
    source_sig = source_signals.get(item.source_name or "")
    source_boost = (
        0.0
        if cold_start or source_sig is None or source_sig.count == 0
        else max(-1.0, min(1.0, source_sig.keep_rate * 2 - 1))
    )
    time_decay = _time_decay(item.published_at)

    # focus hit floor: lift base to 6 when matched
    focus_hits: list[str] = []
    if focus_keywords:
        text = " ".join(
            filter(None, [item.title or "", item.title_cn or "", item.summary_zh or ""])
        )
        from app.processing.keyword_match import matched_keywords

        focus_hits = matched_keywords(focus_keywords, text)
        if focus_hits:
            base = max(base, 6.0)

    final = max(0.0, min(10.0, base + tag_boost + entity_boost + source_boost + time_decay))

    return ScoreBreakdown(
        base=base,
        tag_boost=tag_boost,
        entity_boost=entity_boost,
        source_boost=source_boost,
        time_decay=time_decay,
        final=final,
        cold_start=cold_start,
        focus_hits=focus_hits,
    )
